import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

from livekit.agents import Agent, AgentServer, AgentSession, AutoSubscribe, JobContext, cli, inference, room_io
from livekit.agents.llm import function_tool
from livekit.agents.voice import RunContext
from livekit.plugins import lemonslice

from scoring.models import ConversationTurn, RawTranscript, ToolCall
from scoring.storage import get_storage
from utils import load_prompt

logger = logging.getLogger("lemonslice-salary-coach")
logger.setLevel(logging.INFO)

load_dotenv('.env.local')

server = AgentServer()


@dataclass
class ScenarioConfig:
    """Configuration for each procurement scenario."""
    voice_id: str
    agent_id: str  # LemonSlice agent ID from dashboard
    contract_facts: dict
    vendor_constraints: dict
    outcomes: list
    grounding_rules: dict


# Scenario configurations with unique voices and avatars
SCENARIO_CONFIGS = {
    "scenario_1": ScenarioConfig(
        voice_id="9c8880b2-ccf9-4730-b805-cea23df247d7",  # Selected voice
        agent_id=os.getenv("SCENARIO_1_AGENT_ID", "agent_f8b4dddd8bee7a8a"),
        contract_facts={
            "contract_number": "FA0000-26-P-0123",
            "contract_type": "FFP commercial supply",
            "clin": "0001",
            "item": "Repair kits (generic)",
            "qty": 24,
            "delivery_terms": "30 days ARO",
            "current_status": "supplier backorder",
            "projected_delay_days": 21
        },
        vendor_constraints={
            "base_delay_days": 21,
            "expedite_delay_days": 7,
            "partial_qty_available": 12,
            "max_discount_pct": 8,
            "substitute_available": True
        },
        outcomes=[
            "expedite",
            "partial_shipment",
            "substitute",
            "schedule_extension_with_consideration",
            "impasse_escalate"
        ],
        grounding_rules={
            "must_request_written_notice": True,
            "must_avoid_unilateral_promises": True,
            "preferred_language": [
                "mitigation plan",
                "revised delivery schedule",
                "consideration",
                "modification",
                "sub-tier supplier"
            ]
        }
    ),
    "scenario_2": ScenarioConfig(
        voice_id="228fca29-3a0a-435c-8728-5cb483251068",
        agent_id=os.getenv("SCENARIO_2_AGENT_ID", "agent_f8b4dddd8bee7a8a"),  # Placeholder
        contract_facts={},
        vendor_constraints={},
        outcomes=[],
        grounding_rules={}
    ),
    "scenario_3": ScenarioConfig(
        voice_id="66c6b81c-ddb7-4892-bdd5-19b5a7be38e7",
        agent_id=os.getenv("SCENARIO_3_AGENT_ID", "agent_f8b4dddd8bee7a8a"),  # Placeholder
        contract_facts={},
        vendor_constraints={},
        outcomes=[],
        grounding_rules={}
    ),
}


@dataclass
class UserData:
    """Stores session state for contract negotiation practice."""
    ctx: Optional[JobContext] = None
    scenario_id: str = "scenario_1"
    session_id: str = ""  # Unique session identifier
    participant_id: str = ""  # Participant identifier
    session_start_time: float = 0.0
    timer_task: Optional[asyncio.Task] = None
    session_ended: bool = False
    conversation_turns: list = field(default_factory=list)  # List of conversation turns for transcript capture
    tool_calls: list = field(default_factory=list)  # List of function tool calls for metadata tracking

    def summarize(self) -> str:
        return f"Contract negotiation practice. Scenario: {self.scenario_id}"


RunContext_T = RunContext[UserData]


class BaseVendorAgent(Agent):
    """Base class for all vendor agents - simple negotiation without coaching."""
    
    def __init__(self, instructions: str, tts: inference.TTS) -> None:
        super().__init__(
            instructions=instructions,
            tts=tts,
        )

    async def on_enter(self) -> None:
        """Called when the agent first starts."""
        agent_name = self.__class__.__name__
        logger.info(f"Starting {agent_name}")

        userdata: UserData = self.session.userdata
        if userdata.ctx and userdata.ctx.room:
            await userdata.ctx.room.local_participant.set_attributes({
                "agent": agent_name
            })
        
        # Set up conversation turn tracking
        self._setup_conversation_tracking()
        
        # Start the 3-minute timer if not already started
        if userdata.timer_task is None or userdata.timer_task.done():
            userdata.timer_task = asyncio.create_task(
                self._start_session_timer(userdata, 180) 
            )

    async def on_exit(self) -> None:
        """Called when the agent session ends (disconnect or completion)."""
        userdata: UserData = self.session.userdata
        
        # Cancel timer if still running
        if userdata.timer_task and not userdata.timer_task.done():
            userdata.timer_task.cancel()
            logger.info("Session timer cancelled on exit")
        
        # Calculate session end time and duration
        session_end_time = time.time()
        session_duration = session_end_time - userdata.session_start_time
        
        # Log session stats
        logger.info(
            f"Session ended - Scenario: {userdata.scenario_id}, "
            f"Duration: {session_duration:.1f}s, "
            f"Turns captured: {len(userdata.conversation_turns)}, "
            f"Tool calls: {len(userdata.tool_calls)}"
        )
        
        # Persist transcript to storage
        try:
            # Generate unique session_id if not already set
            if not userdata.session_id:
                userdata.session_id = f"session_{uuid.uuid4().hex[:12]}"
                logger.info(f"Generated session_id: {userdata.session_id}")
            
            # Convert conversation turns to ConversationTurn objects
            turns = [
                ConversationTurn(
                    speaker=turn["speaker"],
                    raw_text=turn["raw_text"],
                    normalized_text=turn["raw_text"],  # Will be normalized later by TranscriptNormalizer
                    timestamp=turn["timestamp"],
                    turn_index=turn["turn_index"]
                )
                for turn in userdata.conversation_turns
            ]
            
            # Convert tool calls to ToolCall objects
            tool_call_objects = [
                ToolCall(
                    tool_name=tc["tool_name"],
                    timestamp=tc["timestamp"],
                    arguments=tc["arguments"],
                    result=tc.get("result")
                )
                for tc in userdata.tool_calls
            ]
            
            # Create RawTranscript object
            transcript = RawTranscript(
                session_id=userdata.session_id,
                scenario_id=userdata.scenario_id,
                session_start_time=userdata.session_start_time,
                session_end_time=session_end_time,
                session_duration=session_duration,
                participant_id=userdata.participant_id or "unknown",
                turns=turns,
                tool_calls=tool_call_objects
            )
            
            # Save transcript to storage
            storage = get_storage()
            storage_path = storage.save_transcript(userdata.session_id, transcript)
            logger.info(f"Transcript persisted to: {storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to persist transcript: {e}", exc_info=True)
            # Don't crash the agent - just log the error

    def _setup_conversation_tracking(self) -> None:
        """Set up event handlers to capture conversation turns."""
        userdata: UserData = self.session.userdata
        
        @self.session.on("user_input_transcribed")
        def on_user_transcript(event):
            """Capture user utterances."""
            if event.is_final:
                turn_index = len(userdata.conversation_turns)
                turn = {
                    "speaker": "trainee",
                    "raw_text": event.transcript,
                    "timestamp": time.time(),
                    "turn_index": turn_index
                }
                userdata.conversation_turns.append(turn)
                logger.debug(f"Captured user turn {turn_index}: {event.transcript[:50]}...")
        
        @self.session.on("agent_speech_committed")
        def on_agent_speech(text: str):
            """Capture agent responses."""
            turn_index = len(userdata.conversation_turns)
            turn = {
                "speaker": "vendor",
                "raw_text": text,
                "timestamp": time.time(),
                "turn_index": turn_index
            }
            userdata.conversation_turns.append(turn)
            logger.debug(f"Captured agent turn {turn_index}: {text[:50]}...")
        
        @self.session.on("function_tool_called")
        def on_tool_call(tool_name: str, arguments: dict, result: Optional[str] = None):
            """Capture function tool invocations."""
            tool_call = {
                "tool_name": tool_name,
                "timestamp": time.time(),
                "arguments": arguments,
                "result": result
            }
            userdata.tool_calls.append(tool_call)
            logger.info(f"Captured tool call: {tool_name} with args {arguments}")

    async def _start_session_timer(self, userdata: UserData, duration: int):
        """Timer that ends the session after specified duration."""
        try:
            await asyncio.sleep(duration)
            if not userdata.session_ended:
                userdata.session_ended = True
                logger.info("Session timer expired - ending session")
                
                await self.session.say(
                    "Our practice session time is up. I hope you have a great day."
                )
                
                # Give time for the speech to be queued and start playing
                await asyncio.sleep(2.0)
                
                # Shutdown the job context to end the session
                if userdata.ctx:
                    userdata.ctx.shutdown("Session timer expired")
        except asyncio.CancelledError:
            logger.info("Session timer cancelled (user disconnected early)")
            # Don't re-raise - this is expected behavior
        except Exception as e:
            logger.error(f"Error in session timer: {e}")


class Scenario1VendorAgent(BaseVendorAgent):
    """Late Delivery of Parts scenario vendor agent - Alex Rivera from Meridian Supply."""
    
    def __init__(self) -> None:
        config = SCENARIO_CONFIGS["scenario_1"]
        
        # Load instructions from YAML file (single source of truth)
        instructions = load_prompt('scenario_1_vendor_prompt.yaml')
        
        super().__init__(
            instructions=instructions,
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id, extra_kwargs={"speed": "normal"})
        )

    async def on_enter(self) -> None:
        """Called when entering the scenario 1 vendor session."""
        await super().on_enter()
        
        # Brief pause to ensure avatar is fully ready for lip sync
        await asyncio.sleep(1.0)
        
        # Generate the opening message
        await self.session.generate_reply(
            instructions='Say the opening line exactly as written in your instructions: "Hi Lieutenant—Alex Rivera, Meridian Supply. Calling about the 24 repair kits. We\'ve hit a supplier delay and the standard lead time pushes delivery out about three weeks. We can pull it back, but only if you\'re willing to cover premium freight and expedite charges. What\'s your direction—revised schedule, or pay to keep the current date?"'
        )


class Scenario2VendorAgent(BaseVendorAgent):
    """Placeholder for Scenario 2 vendor agent."""
    
    def __init__(self) -> None:
        config = SCENARIO_CONFIGS["scenario_2"]
        minimal_instructions = """You are a vendor representative. This is a placeholder scenario."""
        
        super().__init__(
            instructions=minimal_instructions,
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id)
        )

    async def on_enter(self) -> None:
        """Called when entering the scenario 2 vendor session."""
        await super().on_enter()
        # Dashboard agent handles the greeting


class Scenario3VendorAgent(BaseVendorAgent):
    """Placeholder for Scenario 3 vendor agent."""
    
    def __init__(self) -> None:
        config = SCENARIO_CONFIGS["scenario_3"]
        minimal_instructions = """You are a vendor representative. This is a placeholder scenario."""
        
        super().__init__(
            instructions=minimal_instructions,
            tts=inference.TTS("cartesia/sonic-3", voice=config.voice_id)
        )

    async def on_enter(self) -> None:
        """Called when entering the scenario 3 vendor session."""
        await super().on_enter()
        # Dashboard agent handles the greeting
        await super().on_enter()
        
        # Add transcript callback to log what the LLM generates
        def log_agent_speech(text: str):
            logger.info(f"SCENARIO 3 VENDOR LLM OUTPUT: '{text}'")
        
        self.session.on("agent_speech_committed", log_agent_speech)
        
        self.session.generate_reply(
            instructions="Greet the user professionally. This is a placeholder scenario. Use complete sentences."
        )


@server.rtc_session(agent_name="lemonslice-salary-coach")
async def entrypoint(ctx: JobContext):
    """Main entry point for the salary negotiation coach."""
    logger.info("Starting salary negotiation coach session")
    
    # Connect to the room first - subscribe to audio and video for avatar support
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    
    # Wait for participant to connect
    participant = await ctx.wait_for_participant()
    
    # Get scenario_id from participant attributes (default to "scenario_1")
    scenario_id = participant.attributes.get("scenario_id", "scenario_1")
    logger.info(f"Scenario selected: {scenario_id}")
    
    # Validate scenario_id
    if scenario_id not in ["scenario_1", "scenario_2", "scenario_3"]:
        logger.warning(f"Invalid scenario_id '{scenario_id}', defaulting to 'scenario_1'")
        scenario_id = "scenario_1"
    
    # Generate unique session_id
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    
    # Get participant_id (use participant identity or generate one)
    participant_id = participant.identity or f"participant_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Session initialized - session_id: {session_id}, participant_id: {participant_id}")
    
    # Get scenario configuration for avatar and voice
    scenario_config = SCENARIO_CONFIGS[scenario_id]
    
    # Initialize user data
    userdata = UserData(
        ctx=ctx,
        scenario_id=scenario_id,
        session_id=session_id,
        participant_id=participant_id,
        session_start_time=time.time()
    )
    
    # Create the appropriate vendor agent
    if scenario_id == "scenario_1":
        vendor_agent = Scenario1VendorAgent()
    elif scenario_id == "scenario_2":
        vendor_agent = Scenario2VendorAgent()
    else:  # scenario_3
        vendor_agent = Scenario3VendorAgent()
    
    # Optional: Start lemonslice avatar (can be disabled for debugging)
    # Set ENABLE_LEMONSLICE_AVATAR=false in .env.local to disable avatar
    enable_avatar = os.getenv("ENABLE_LEMONSLICE_AVATAR", "true").lower() == "true"
    
    # Create session with userdata
    session = AgentSession[UserData](
        stt=inference.STT("deepgram/nova-3"),
        llm=inference.LLM("openai/gpt-4o-mini"),
        tts=inference.TTS("cartesia/sonic-3", voice=scenario_config.voice_id, extra_kwargs={"speed": "normal"}),  # normal speech
        resume_false_interruption=False,
        userdata=userdata
    )
    
    if enable_avatar:
        logger.info("LemonSlice avatar enabled - starting avatar session")
        # Start lemonslice avatar with scenario-specific agent ID from dashboard
        # idle_timeout set to 300 seconds (5 minutes) to prevent avatar disconnection
        # during the 180-second (3-minute) session duration
        avatar = lemonslice.AvatarSession(
            agent_id=scenario_config.agent_id,
            idle_timeout=300,
        )
        # Start avatar and wait for it to be ready
        # The avatar.start() method handles waiting for the participant and video track
        await avatar.start(session, room=ctx.room)
        logger.info("Avatar session started and ready")
    else:
        logger.info("LemonSlice avatar disabled (ENABLE_LEMONSLICE_AVATAR=false) - audio-only mode")
    
    # Start directly with the selected vendor agent
    await session.start(
        agent=vendor_agent,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            delete_room_on_close=True,
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)

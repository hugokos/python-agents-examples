# LemonSlice contract negotiation trainer

This agent creates an interactive procurement contract negotiation practice experience using [LemonSlice](https://www.lemonslice.com/) avatars with LiveKit Agents. Users can practice handling contract scenarios with different vendor personas, and get real-time coaching feedback.

## Setup

### Environment variables

Create a `.env.local` file in this directory with the following variables:

```bash
# LiveKit Configuration (also used for inference API)
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

LEMONSLICE_API_KEY=your_lemonslice_api_key

# LemonSlice Agent IDs (use dashboard-configured agents)
# These reference agents you've created in your LemonSlice dashboard
SCENARIO_1_AGENT_ID=agent_f8b4dddd8bee7a8a
# SCENARIO_2_AGENT_ID=agent_your_second_agent_id
# SCENARIO_3_AGENT_ID=agent_your_third_agent_id
```

### Dependencies

Install dependencies using uv:

```bash
uv sync
```

This will install:
- `livekit-agents` (>=1.3.12)
- `livekit-plugins-lemonslice` (>=1.3.12)
- `python-dotenv`
- `pyyaml`

### Running the agent

Start the agent worker in development mode:

```bash
uv run lemonslice-agent.py dev
```

## Features

### Three procurement scenarios

Each scenario has a unique voice, avatar, and contract situation:

- **Scenario 1 (Late Delivery of Parts)**: Vendor calls about a delayed shipment. Practice handling contract issues professionally and learning procurement communication fundamentals.
- **Scenario 2 (Coming Soon)**: Additional procurement scenario in development.
- **Scenario 3 (Coming Soon)**: Additional procurement scenario in development.

### Dual-mode operation

- **Roleplay mode**: Practice negotiating with the vendor persona
- **Coaching mode**: Get real-time feedback on your performance by asking "How am I doing?"

### Session management

- 3-minute practice sessions with automatic timer
- Session ends with a summary after time expires
- Tracks coaching requests and negotiation phases

### Models and services

- **Speech-to-Text**: Deepgram Nova 3 (via LiveKit inference API)
- **Language Model**: Google Gemini 2.5 Flash (via LiveKit inference API)
- **Text-to-Speech**: Cartesia Sonic 3 (via LiveKit inference API)
- **Avatar**: LemonSlice animated avatars with personality-specific movement prompts

## How it works

1. User selects a procurement scenario in the frontend (scenario_1, scenario_2, or scenario_3)
2. Agent receives scenario ID via participant attributes
3. Agent creates appropriate `BaseVendorAgent` subclass with scenario-specific:
   - Instructions loaded from YAML prompt files
   - Cartesia voice ID
   - LemonSlice agent ID (references dashboard-configured avatar)
4. `AgentSession` starts with the selected vendor agent
5. LemonSlice `AvatarSession` publishes synchronized audio + video tracks using the dashboard agent
6. Vendor agent greets user and begins roleplay
7. User can trigger coaching mode via function tool `how_am_i_doing()`
8. Agent switches modes by updating instructions dynamically
9. After 3 minutes, session automatically ends with a farewell message

## Architecture

### Agent classes

- `BaseVendorAgent`: Base class with coaching functionality and mode switching
  - `Scenario1VendorAgent`: Late Delivery of Parts scenario
  - `Scenario2VendorAgent`: Placeholder for future scenario
  - `Scenario3VendorAgent`: Placeholder for future scenario

### Function tools

- `how_am_i_doing()`: Switches from roleplay to coaching mode
- `return_to_roleplay()`: Returns from coaching back to vendor roleplay

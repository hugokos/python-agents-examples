export type ScenarioId = 'scenario_1' | 'scenario_2' | 'scenario_3';

export interface ScenarioDefinition {
  id: ScenarioId;
  title: string;
  description: string;
  imageUrl: string;
  available: boolean;
  color: string;
  borderColor: string;
  bgColor: string;
  textColor: string;
}

export const SCENARIOS: Record<ScenarioId, ScenarioDefinition> = {
  scenario_1: {
    id: 'scenario_1',
    title: 'Late Delivery of Parts',
    description: 'Vendor calls about a delayed shipment. Practice handling contract issues professionally.',
    imageUrl: '/img/vendor_avatar.png',  // Update this image to match your LemonSlice avatar
    available: true,
    color: 'blue',
    borderColor: 'border-blue-500',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-500',
  },
  scenario_2: {
    id: 'scenario_2',
    title: 'Coming Soon',
    description: 'Additional procurement scenario in development.',
    imageUrl: '/img/scenario_placeholder.png',
    available: false,
    color: 'gray',
    borderColor: 'border-gray-500',
    bgColor: 'bg-gray-500/10',
    textColor: 'text-gray-500',
  },
  scenario_3: {
    id: 'scenario_3',
    title: 'Coming Soon',
    description: 'Additional procurement scenario in development.',
    imageUrl: '/img/scenario_placeholder.png',
    available: false,
    color: 'gray',
    borderColor: 'border-gray-500',
    bgColor: 'bg-gray-500/10',
    textColor: 'text-gray-500',
  },
};

export const MODE_COLORS = {
  roleplay: {
    borderColor: 'border-blue-500',
    bgColor: 'bg-blue-500/10',
    textColor: 'text-blue-500',
    label: 'Role-play mode',
  },
  coaching: {
    borderColor: 'border-green-500',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-500',
    label: 'Coaching mode',
  },
};

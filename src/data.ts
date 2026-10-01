export const DESIGNATIONS = [
  'Student',
  'Faculty',
  'Research Scholar',
  'Lab In-charge',
  'Head of Department',
  'External Researcher',
] as const;

export const DEPARTMENTS = [
  'Computer Science and Engineering',
  'Artificial Intelligence and Data Science',
  'Information Technology',
  'Electronics and Communication Engineering',
  'Electrical and Electronics Engineering',
  'Mechanical Engineering',
  'Civil Engineering',
  'Computer Science and Business Systems',
  'Electronics and Instrumentation Engineering',
] as const;

export const LAB_CATALOG = {
  'Advanced Computing & AI Lab': [
    'GPU Workstation — NVIDIA A100',
    'High-Performance Compute Node',
    'Deep Learning Training Server',
    'Data Annotation Workstation',
  ],
  'IoT & Embedded Systems Lab': [
    'IoT Gateway Test Bench',
    'ARM Cortex Development Kit',
    'Sensor Fusion Rig',
    'PCB Prototyping Station',
  ],
  'VLSI & Electronics Lab': [
    'FPGA Development Board',
    'Mixed-Signal Oscilloscope',
    'Logic Analyzer',
    'Spectrum Analyzer',
  ],
  'Materials Characterization Lab': [
    'Universal Testing Machine',
    'Optical Microscope',
    'Hardness Tester',
    'Thermal Analysis Station',
  ],
  'CAD / CAM & Prototyping Lab': [
    '3D Printer — FDM',
    'CNC Milling Station',
    'CAD Workstation',
    'Coordinate Measuring Arm',
  ],
  'Renewable Energy Lab': [
    'Solar PV Test Bench',
    'Wind Energy Trainer',
    'Power Quality Analyzer',
    'Battery Characterization Unit',
  ],
  'Communication & Signal Processing Lab': [
    'Software-Defined Radio Kit',
    'Vector Network Analyzer',
    'DSP Development Board',
    'Antenna Measurement Setup',
  ],
} as const;

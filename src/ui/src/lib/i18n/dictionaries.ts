/** Typed ES/EN dictionaries for the digital twin UI. */

export type Language = "en" | "es";

export interface Dictionary {
  header: {
    title: string;
    subtitle: string;
  };
  metrics: {
    surface: string;
    bit: string;
    torsion: string;
    rpm: string;
    ssi: string;
    rpmTitle: string;
    surfaceEst: string;
    bitEst: string;
    status: {
      live: string;
      connecting: string;
      disconnected: string;
      error: string;
    };
  };
  ssiRegimes: {
    normal: string;
    warning: string;
    critical: string;
  };
  ssiGauge: {
    title: string;
  };
  advisor: {
    title: string;
    subtitle: string;
    empty: string;
    incidentType: string;
    severityLevel: string;
    physicalRootCause: string;
    immediateActions: string;
    targetWob: string;
    targetRpm: string;
    rationale: string;
  };
  simulationControls: {
    title: string;
    start: string;
    stop: string;
    running: string;
    simTime: string;
    mwdDrops: string;
  };
  loading3d: string;
}

export const en: Dictionary = {
  header: {
    title: "Drillstring Digital Twin",
    subtitle: "Torsional deformation · SSI · LLM Advisor (soft real-time)",
  },
  metrics: {
    surface: "Surface",
    bit: "Bit",
    torsion: "Torsion",
    rpm: "RPM",
    ssi: "SSI",
    rpmTitle: "RPM Surface vs Bit",
    surfaceEst: "Surface (est.)",
    bitEst: "Bit (est.)",
    status: {
      live: "Live",
      connecting: "Connecting",
      disconnected: "Disconnected",
      error: "Error",
    },
  },
  ssiRegimes: {
    normal: "NORMAL",
    warning: "WARNING",
    critical: "CRITICAL",
  },
  ssiGauge: {
    title: "SSI Gauge",
  },
  advisor: {
    title: "LLM Advisor Feed",
    subtitle: "SOP mitigations on SSI > 1.0 events",
    empty: "No recommendations yet.",
    incidentType: "Incident type",
    severityLevel: "Severity",
    physicalRootCause: "Physical root cause",
    immediateActions: "Immediate actions",
    targetWob: "Target WOB",
    targetRpm: "Target RPM",
    rationale: "Rationale",
  },
  simulationControls: {
    title: "Simulation Control",
    start: "Start",
    stop: "Stop",
    running: "running",
    simTime: "t",
    mwdDrops: "drops",
  },
  loading3d: "Loading 3D twin…",
};

export const es: Dictionary = {
  header: {
    title: "Gemelo Digital de Sarta",
    subtitle: "Deformación torsional · SSI · Asesor IA (tiempo real)",
  },
  metrics: {
    surface: "Superficie",
    bit: "Broca",
    torsion: "Torsión",
    rpm: "RPM",
    ssi: "SSI",
    rpmTitle: "RPM Superficie vs Broca",
    surfaceEst: "Superficie (est.)",
    bitEst: "Broca (est.)",
    status: {
      live: "En vivo",
      connecting: "Conectando",
      disconnected: "Desconectado",
      error: "Error",
    },
  },
  ssiRegimes: {
    normal: "NORMAL",
    warning: "ADVERTENCIA",
    critical: "Stick-Slip Crítico",
  },
  ssiGauge: {
    title: "Indicador SSI",
  },
  advisor: {
    title: "Feed del Asesor IA",
    subtitle: "Mitigaciones SOP en eventos SSI > 1.0",
    empty: "Sin recomendaciones aún.",
    incidentType: "Tipo de incidente",
    severityLevel: "Severidad",
    physicalRootCause: "Causa raíz física",
    immediateActions: "Acciones inmediatas",
    targetWob: "WOB objetivo",
    targetRpm: "RPM objetivo",
    rationale: "Justificación",
  },
  simulationControls: {
    title: "Control de Simulación",
    start: "Iniciar",
    stop: "Detener",
    running: "corriendo",
    simTime: "t",
    mwdDrops: "caídas",
  },
  loading3d: "Cargando gemelo 3D…",
};

const DICTIONARIES: Record<Language, Dictionary> = { en, es };

export function getDictionary(locale: Language): Dictionary {
  return DICTIONARIES[locale];
}

export function isLanguage(value: string): value is Language {
  return value === "en" || value === "es";
}

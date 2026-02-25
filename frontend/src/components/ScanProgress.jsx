import { useState, useEffect } from "react";

export default function ScanProgress() {
  const [completedSteps, setCompletedSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { label: "Initializing Tor Browser", duration: 800 },
    { label: "Establishing SOCKS5 Proxy Connection", duration: 1200 },
    { label: "Connecting to Tor Network", duration: 1500 },
    { label: "Resolving .onion Address", duration: 900 },
    { label: "Fetching Page Content", duration: 1800 },
    { label: "Parsing HTML Structure", duration: 700 },
    { label: "Extracting IOCs (URLs, IPs, Emails)", duration: 1000 },
    { label: "Analyzing Threat Indicators", duration: 1100 },
    { label: "Scanning for Malware Signatures", duration: 1300 },
    { label: "Checking ClamAV Database", duration: 900 },
    { label: "Calculating Threat Score", duration: 600 },
    { label: "Connecting to MongoDB Atlas", duration: 700 },
    { label: "Storing Scan Results", duration: 500 },
    { label: "Finalizing Analysis", duration: 400 },
  ];

  useEffect(() => {
    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setCompletedSteps(prev => [...prev, currentStep]);
        setCurrentStep(prev => prev + 1);
      }, steps[currentStep].duration);

      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const getIcon = (iconType) => {
    if (iconType === "completed") {
      return (
        <svg className="h-4 w-4 text-neon-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    }
    if (iconType === "loading") {
      return (
        <svg className="h-4 w-4 text-neon-blue animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      );
    }
    return null;
  };

  const getCurrentStepDisplay = () => {
    if (currentStep >= steps.length) {
      return {
        label: "Scan Complete",
        isComplete: true
      };
    }
    return {
      label: steps[currentStep].label,
      isComplete: false,
      stepNumber: currentStep + 1
    };
  };

  const stepDisplay = getCurrentStepDisplay();

  return (
    <div className="flex flex-col items-center justify-center gap-8 py-12 w-full max-w-2xl mx-auto">
      {/* Main spinner and title */}
      <div className="flex flex-col items-center gap-4">
        {!stepDisplay.isComplete ? (
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-neon-blue/40 border-t-neon-blue" />
        ) : (
          <div className="h-16 w-16 flex items-center justify-center rounded-full bg-neon-green/20 border-4 border-neon-green/40">
            <svg className="h-8 w-8 text-neon-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        <div className="text-center">
          <p className="text-xl font-semibold text-neon-blue mb-1">
            {stepDisplay.isComplete ? "Scan Complete" : "Scanning in Progress"}
          </p>
          {!stepDisplay.isComplete && (
            <p className="text-sm text-gray-500">
              Step {stepDisplay.stepNumber} of {steps.length}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-2 flex-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-neon-blue to-neon-green transition-all duration-500 ease-out"
              style={{ width: `${(completedSteps.length / steps.length) * 100}%` }}
            />
          </div>
          <span className="text-sm text-gray-400 font-mono min-w-[50px] text-right">
            {Math.round((completedSteps.length / steps.length) * 100)}%
          </span>
        </div>
      </div>

      {/* Current step display - single line that updates */}
      <div className="w-full bg-gray-900/60 rounded-lg border border-white/10 p-6 min-h-[100px] flex items-center justify-center">
        <div className="flex items-center gap-3 w-full">
          <div className="flex-shrink-0">
            {stepDisplay.isComplete ? (
              <svg className="h-6 w-6 text-neon-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="h-6 w-6 text-neon-blue animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            )}
          </div>
          <div className="flex-1">
            <p className={`text-base font-mono transition-all duration-300 ${
              stepDisplay.isComplete ? "text-neon-green" : "text-neon-blue"
            }`}>
              {stepDisplay.label}
            </p>
          </div>
          {!stepDisplay.isComplete && (
            <div className="flex gap-1.5 flex-shrink-0">
              <span className="h-2 w-2 animate-bounce rounded-full bg-neon-blue" style={{ animationDelay: "0ms" }} />
              <span className="h-2 w-2 animate-bounce rounded-full bg-neon-blue" style={{ animationDelay: "150ms" }} />
              <span className="h-2 w-2 animate-bounce rounded-full bg-neon-blue" style={{ animationDelay: "300ms" }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

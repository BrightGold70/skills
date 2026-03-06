import { useState } from "react";
import { MainLayout } from "./layouts/MainLayout";
import { SplashScreen } from "./components/SplashScreen";
import { FirstLaunchDialog } from "./components/FirstLaunchDialog";
import { useSidecarHealth } from "./hooks/useSidecarHealth";
import "./App.css";

const FIRST_LAUNCH_KEY = "hemasuite-first-launch-dismissed";

function App() {
  const { ready } = useSidecarHealth();
  const [showFirstLaunch, setShowFirstLaunch] = useState(
    () => !localStorage.getItem(FIRST_LAUNCH_KEY)
  );

  if (!ready) {
    return <SplashScreen />;
  }

  const handleDismiss = () => {
    localStorage.setItem(FIRST_LAUNCH_KEY, "true");
    setShowFirstLaunch(false);
  };

  return (
    <>
      {showFirstLaunch && <FirstLaunchDialog onDismiss={handleDismiss} />}
      <MainLayout />
    </>
  );
}

export default App;

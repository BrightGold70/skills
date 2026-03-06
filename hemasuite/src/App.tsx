import { MainLayout } from "./layouts/MainLayout";
import { SplashScreen } from "./components/SplashScreen";
import { useSidecarHealth } from "./hooks/useSidecarHealth";
import "./App.css";

function App() {
  const { ready } = useSidecarHealth();

  if (!ready) {
    return <SplashScreen />;
  }

  return <MainLayout />;
}

export default App;

import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";

export interface MenuHandlers {
  onNewProject: () => void;
  onOpenProject: () => void;
  onSave: () => void;
}

export function useMenuEvents(handlers: MenuHandlers) {
  useEffect(() => {
    const unlistenPromise = listen<string>("menu-event", (event) => {
      switch (event.payload) {
        case "new-project":
          handlers.onNewProject();
          break;
        case "open-project":
          handlers.onOpenProject();
          break;
        case "save":
          handlers.onSave();
          break;
      }
    });

    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  }, [handlers]);
}

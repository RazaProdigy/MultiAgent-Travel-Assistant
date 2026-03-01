import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatInterface from "./components/ChatInterface";
import SupervisorPanel from "./components/SupervisorPanel";

function App() {
  return (
    <div className="App bg-[#dad3cc] min-h-screen">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ChatInterface />} />
          <Route path="/supervisor/:sessionId" element={<SupervisorPanel />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;

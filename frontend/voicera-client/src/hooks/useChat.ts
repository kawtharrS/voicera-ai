import { useState, useRef, useCallback } from "react";
import api from "../api/axios";

interface Message {
    sender: "user" | "ai";
    text: string;
    category: string;
    recommendations?: string[];
    imageUrl?: string;
}


export const useChat = (onResponse: (text: string, category: string) => void) => {
    const [input, setInput] = useState("");
    const [waiting, setWaiting] = useState(false);
    const [currentCategory, setCurrentCategory] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([
        {
            sender: "ai",
            text: "Hi! Ask me anything about study, work, or personal topics.",
            category: "greeting",
        },
    ]);

    const sessionId = useRef(
        crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7)
    );

    const sendMessage = useCallback(
        async (text: string) => {
            if (!text.trim() || waiting) return;

            const userMessage = text.trim();
            setMessages((prev) => [...prev, { sender: "user", text: userMessage, category: "user" }]);
            setInput("");
            setWaiting(true);

            try {
                let preferences: any = null;
                try {
                    if (typeof window !== "undefined") {
                        const raw = window.localStorage.getItem("voicera_prefs");
                        if (raw) {
                            preferences = JSON.parse(raw);
                        }
                    }
                } catch (e) {
                    console.error("Failed to read saved preferences", e);
                }

                const payload: any = {
                    question: userMessage,
                    thread_id: `session_${sessionId.current}`,
                };

                if (preferences) {
                    payload.preferences = {
                        language: preferences.language,
                        tone: preferences.tone,
                        agent_name: preferences.agentName,
                        memory_notes: preferences.memoryNotes,
                    };
                }

                const response = await api.post<any>("/ask-anything", payload);
                const responseData = response.data;
                const data = responseData.data || responseData;

                const aiText = data.response || (data as any).ai_response || "No answer received.";
                const category = data.category || "unknown";
                const recommendations = data.recommendations || [];
                // Emotion is still extracted by the backend and saved in memory,
                // but it is not needed in the web UI state here.

                setCurrentCategory(category);
                setMessages((prev) => [
                    ...prev,
                    { sender: "ai", text: aiText, category, recommendations },
                ]);

                onResponse(aiText, category);

            } catch (error: any) {
                let errorText = "Sorry, there was an error.";
                if (error.response?.status === 404) {
                    errorText = "Endpoint /ask-anything not found.";
                } else if (error.response?.status === 500) {
                    errorText = `Server error: ${error.response?.data?.detail || "Unknown error"}`;
                }
                setMessages((prev) => [...prev, { sender: "ai", text: errorText, category: "error" }]);
                onResponse(errorText, "error");
            } finally {
                setWaiting(false);
            }
        },
        [waiting, onResponse]
    );

    const addMessage = useCallback((sender: "user" | "ai", text: string, category: string, imageUrl?: string) => {
        setMessages((prev) => [...prev, { sender, text, category, imageUrl }]);
    }, []);

    return {
        input,
        setInput,
        messages,
        waiting,
        currentCategory,
        sendMessage,
        addMessage,
    };
};

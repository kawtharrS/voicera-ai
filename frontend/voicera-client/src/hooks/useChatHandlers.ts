import { useState, useEffect, useRef, useCallback } from "react";
import api from "../api/axios";

interface UseChatHandlersProps {
    sendMessage: (text: string) => Promise<void>;
    startRecording: () => void;
    stopRecording: () => void;
    resetTranscript: () => void;
    finalTranscript: string;
    interimTranscript: string;
    isRecording: boolean;
    isDragging: boolean;
}

export const useChatHandlers = ({
    sendMessage,
    startRecording,
    stopRecording,
    resetTranscript,
    finalTranscript,
    interimTranscript,
    isRecording,
    isDragging,
}: UseChatHandlersProps) => {
    const [roleId, setRoleId] = useState<number | null>(null);
    const [isSending, setIsSending] = useState(false);
    const recentlyDragged = useRef(false);

    useEffect(() => {
        api.get("/user")
            .then((r) => setRoleId(r.data.role_id || 1))
            .catch(() => setRoleId(1));
    }, []);

    const handleSendVoice = useCallback(async () => {
        const fullText = (finalTranscript + interimTranscript).trim();
        if (fullText) {
            setIsSending(true);
            try {
                await sendMessage(fullText);
                resetTranscript();
            } finally {
                setIsSending(false);
            }
        }
    }, [finalTranscript, interimTranscript, sendMessage, resetTranscript]);

    const handleToggleVoice = useCallback(() => {
        if (recentlyDragged.current) return;
        if (isRecording) {
            stopRecording();
            setTimeout(handleSendVoice, 500);
        } else {
            startRecording();
        }
    }, [isRecording, stopRecording, startRecording, handleSendVoice]);

    const updateRecentlyDragged = (value: boolean) => {
        recentlyDragged.current = value;
    };

    return {
        roleId,
        isSending,
        recentlyDragged,
        handleSendVoice,
        handleToggleVoice,
        updateRecentlyDragged,
    };
};

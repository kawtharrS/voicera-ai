import { useState, useRef, useEffect, useCallback } from "react";

export const useSpeechRecognition = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [interimTranscript, setInterimTranscript] = useState("");
    const [finalTranscript, setFinalTranscript] = useState("");
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition || recognitionRef.current) return;

        const rec = new SpeechRecognition();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = "en-US";

        rec.onstart = () => setIsRecording(true);
        rec.onresult = (e: any) => {
            let interim = "";
            for (let i = e.resultIndex; i < e.results.length; i++) {
                const transcript = e.results[i][0].transcript;
                if (e.results[i].isFinal) setFinalTranscript((prev) => prev + transcript + " ");
                else interim += transcript;
            }
            setInterimTranscript(interim);
        };
        rec.onerror = () => setIsRecording(false);
        rec.onend = () => setIsRecording(false);

        recognitionRef.current = rec;
    }, []);

    const startRecording = useCallback(() => {
        if (recognitionRef.current && !isRecording) {
            setFinalTranscript("");
            setInterimTranscript("");
            recognitionRef.current.start();
        }
    }, [isRecording]);

    const stopRecording = useCallback(() => {
        if (recognitionRef.current && isRecording) {
            recognitionRef.current.stop();
        }
    }, [isRecording]);

    const resetTranscript = useCallback(() => {
        setFinalTranscript("");
        setInterimTranscript("");
    }, []);

    return {
        isRecording,
        interimTranscript,
        finalTranscript,
        startRecording,
        stopRecording,
        resetTranscript,
    };
};

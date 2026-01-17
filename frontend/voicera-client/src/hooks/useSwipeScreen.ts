import { useState, useRef, useEffect, useCallback } from "react";

export const useSwipeScreen = () => {
    const [position, setPosition] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [isSecondScreenActive, setIsSecondScreenActive] = useState(false);
    const startY = useRef(0);
    const currentY = useRef(0);

    const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
        setIsDragging(true);
        startY.current = e.touches[0].clientY;
        currentY.current = position;
    };

    const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
        if (!isDragging) return;
        const deltaY = e.touches[0].clientY - startY.current;
        const newPosition = Math.max(
            -100,
            Math.min(0, currentY.current + (deltaY / window.innerHeight) * 100)
        );
        setPosition(newPosition);
    };

    const handleTouchEnd = () => {
        setIsDragging(false);
        const isOpening = position < -30;
        setPosition(isOpening ? -100 : 0);
        setIsSecondScreenActive(isOpening);
    };

    const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
        setIsDragging(true);
        startY.current = e.clientY;
        currentY.current = position;
    };

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!isDragging) return;
        const deltaY = e.clientY - startY.current;
        const newPosition = Math.max(
            -100,
            Math.min(0, currentY.current + (deltaY / window.innerHeight) * 100)
        );
        setPosition(newPosition);
    };

    const handleMouseUp = () => {
        setIsDragging(false);
        const isOpening = position < -30;
        setPosition(isOpening ? -100 : 0);
        setIsSecondScreenActive(isOpening);
    };

    const openSecondScreen = useCallback(() => {
        setPosition(-100);
        setIsSecondScreenActive(true);
    }, []);

    const closeSecondScreen = useCallback(() => {
        setPosition(0);
        setIsSecondScreenActive(false);
    }, []);

    return {
        position,
        isDragging,
        isSecondScreenActive,
        handleTouchStart,
        handleTouchMove,
        handleTouchEnd,
        handleMouseDown,
        handleMouseMove,
        handleMouseUp,
        openSecondScreen,
        closeSecondScreen,
    };
};

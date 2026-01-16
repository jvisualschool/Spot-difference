import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface GameBoardProps {
    originalSrc: string;
    modifiedSrc: string;
    differences: any[];
    onImageClick: (x: number, y: number) => void;
    gameState: string;
    wrongEffect: { x: number, y: number } | null;
}

const GameBoard: React.FC<GameBoardProps> = ({
    originalSrc,
    modifiedSrc,
    differences,
    onImageClick,
    gameState,
    wrongEffect
}) => {
    const [aspectRatio, setAspectRatio] = React.useState<number>(1); // Default to square

    const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
        const { naturalWidth, naturalHeight } = e.currentTarget;
        setAspectRatio(naturalWidth / naturalHeight);
    };

    const isWide = aspectRatio > 1.2; // 16:9 is ~1.77, Square is 1.0

    const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
        if (gameState !== 'playing') return;

        // Get the img element inside this container
        const container = e.currentTarget;
        const img = container.querySelector('img');
        if (!img) return;

        const imgRect = img.getBoundingClientRect();

        // Calculate click position relative to the image
        const x = e.clientX - imgRect.left;
        const y = e.clientY - imgRect.top;

        // Ensure click is within image bounds
        if (x < 0 || y < 0 || x > imgRect.width || y > imgRect.height) {
            console.log('Click outside image bounds');
            return;
        }

        // Scale to 1024x1024 coordinates based on actual image dimensions
        const scaledX = (x / imgRect.width) * 1024;
        const scaledY = (y / imgRect.height) * 1024;

        console.log('Image size:', imgRect.width, imgRect.height);
        console.log('Click position:', x, y);
        console.log('Scaled coordinates:', scaledX, scaledY);

        onImageClick(scaledX, scaledY);
    };

    const renderMarkers = () => {
        return differences.map(diff => {
            if (!diff.found) return null;

            const box = typeof diff.bounding_box === 'object' && !Array.isArray(diff.bounding_box)
                ? diff.bounding_box
                : { x1: diff.bounding_box[0], y1: diff.bounding_box[1], x2: diff.bounding_box[2], y2: diff.bounding_box[3] };

            // Percentage based on 1024x1024
            const left = (box.x1 / 1024) * 100;
            const top = (box.y1 / 1024) * 100;
            const width = ((box.x2 - box.x1) / 1024) * 100;
            const height = ((box.y2 - box.y1) / 1024) * 100;

            return (
                <div
                    key={diff.id}
                    style={{
                        position: 'absolute',
                        left: `${left}%`,
                        top: `${top}%`,
                        width: `${width}%`,
                        height: `${height}%`,
                        border: '0.4vw solid #fbbf24',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        pointerEvents: 'none',
                        zIndex: 20,
                        boxShadow: '0 0 0 0.15vw rgba(251, 191, 36, 0.3)',
                        filter: 'url(#crayon-filter)',
                    }}
                />
            );
        });
    };

    const renderWrongEffect = () => {
        if (!wrongEffect) return null;
        const leftPercent = (wrongEffect.x / 1024) * 100;
        const topPercent = (wrongEffect.y / 1024) * 100;

        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{
                    position: 'absolute',
                    left: `${leftPercent}%`,
                    top: `${topPercent}%`,
                    transform: 'translate(-50%, -100%)',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    whiteSpace: 'nowrap',
                    zIndex: 30,
                    pointerEvents: 'none',
                }}
            >
                오답! ({Math.round(wrongEffect.x)}, {Math.round(wrongEffect.y)})
            </motion.div>
        );
    };

    const ImageWithOverlay = ({ src, alt, isOriginal }: { src: string; alt: string; isOriginal: boolean }) => (
        <div className="image-wrapper">
            <div
                className={`image-badge ${isOriginal ? 'badge-original' : 'badge-modified'}`}
            >
                {isOriginal ? 'Original' : 'Modified'}
            </div>
            <div
                onPointerDown={handlePointerDown}
                style={{
                    position: 'relative',
                    display: 'inline-block',
                }}
            >
                <img
                    src={src}
                    alt={alt}
                    onLoad={isOriginal ? handleImageLoad : undefined}
                    draggable={false}
                    className="game-image"
                />
                {/* Markers overlay - absolutely positioned relative to parent */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    pointerEvents: 'none',
                }}>
                    {renderMarkers()}
                    <AnimatePresence>
                        {renderWrongEffect()}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );

    return (
        <div className={`game-board-container ${isWide ? 'layout-vertical' : 'layout-horizontal'}`}>
            {/* SVG Filter for crayon effect */}
            <svg style={{ position: 'absolute', width: 0, height: 0 }}>
                <defs>
                    <filter id="crayon-filter">
                        <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="5" result="noise" />
                        <feDisplacementMap in="SourceGraphic" in2="noise" scale="3" xChannelSelector="R" yChannelSelector="G" />
                    </filter>
                </defs>
            </svg>
            <ImageWithOverlay src={originalSrc} alt="Original" isOriginal={true} />
            <ImageWithOverlay src={modifiedSrc} alt="Modified" isOriginal={false} />
        </div>
    );
};

export default GameBoard;

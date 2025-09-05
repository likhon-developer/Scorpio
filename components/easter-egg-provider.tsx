'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useTheme } from 'next-themes';

interface EasterEggContextType {
  isEasterEggActive: boolean;
  konamiProgress: number;
  activateEasterEgg: () => void;
  resetEasterEgg: () => void;
}

const EasterEggContext = createContext<EasterEggContextType | undefined>(undefined);

const KONAMI_CODE = [
  'ArrowUp',
  'ArrowUp',
  'ArrowDown',
  'ArrowDown',
  'ArrowLeft',
  'ArrowRight',
  'ArrowLeft',
  'ArrowRight',
  'KeyB',
  'KeyA',
];

export function EasterEggProvider({ children }: { children: React.ReactNode }) {
  const [isEasterEggActive, setIsEasterEggActive] = useState(false);
  const [konamiProgress, setKonamiProgress] = useState(0);
  const { setTheme } = useTheme();

  const activateEasterEgg = () => {
    setIsEasterEggActive(true);
    setTheme('dark');
    
    // Add visual feedback
    document.body.classList.add('easter-egg-active');
    
    // Create particle effect
    createParticleEffect();
    
    // Show notification
    showEasterEggNotification();
  };

  const resetEasterEgg = () => {
    setIsEasterEggActive(false);
    setKonamiProgress(0);
    document.body.classList.remove('easter-egg-active');
  };

  const createParticleEffect = () => {
    const colors = ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
    
    for (let i = 0; i < 20; i++) {
      const particle = document.createElement('div');
      particle.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        width: 4px;
        height: 4px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        border-radius: 50%;
        pointer-events: none;
        z-index: 9999;
        transform: translate(-50%, -50%);
        animation: particle-fade 2s ease-out forwards;
      `;
      
      document.body.appendChild(particle);
      
      const angle = (Math.PI * 2 * i) / 20;
      const velocity = 100 + Math.random() * 100;
      
      particle.style.setProperty('--dx', `${Math.cos(angle) * velocity}px`);
      particle.style.setProperty('--dy', `${Math.sin(angle) * velocity}px`);
      
      setTimeout(() => particle.remove(), 2000);
    }
  };

  const showEasterEggNotification = () => {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
      z-index: 10000;
      font-family: system-ui, sans-serif;
      font-weight: 600;
      animation: slide-in 0.3s ease-out;
    `;
    notification.textContent = '🎮 Easter Egg Activated! Dark mode enabled!';
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slide-out 0.3s ease-out forwards';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  };

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.code === KONAMI_CODE[konamiProgress]) {
        setKonamiProgress(prev => prev + 1);
        
        if (konamiProgress + 1 === KONAMI_CODE.length) {
          activateEasterEgg();
          setKonamiProgress(0);
        }
      } else {
        setKonamiProgress(0);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [konamiProgress]);

  return (
    <EasterEggContext.Provider
      value={{
        isEasterEggActive,
        konamiProgress,
        activateEasterEgg,
        resetEasterEgg,
      }}
    >
      {children}
    </EasterEggContext.Provider>
  );
}

export function useEasterEgg() {
  const context = useContext(EasterEggContext);
  if (context === undefined) {
    throw new Error('useEasterEgg must be used within an EasterEggProvider');
  }
  return context;
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes particle-fade {
    0% {
      opacity: 1;
      transform: translate(-50%, -50%) scale(1);
    }
    100% {
      opacity: 0;
      transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) scale(0);
    }
  }

  @keyframes slide-in {
    from {
      opacity: 0;
      transform: translateX(100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes slide-out {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 0;
      transform: translateX(100%);
    }
  }

  body.easter-egg-active {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  }

  .easter-egg-active * {
    transition: all 0.3s ease-in-out;
  }
`;

if (typeof document !== 'undefined') {
  document.head.appendChild(style);
}

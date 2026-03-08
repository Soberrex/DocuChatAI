import { useState, useEffect } from 'react';

type Breakpoint = 'mobile' | 'tablet' | 'desktop';

export function useResponsive() {
    const getBreakpoint = (): Breakpoint => {
        const w = window.innerWidth;
        if (w < 640) return 'mobile';
        if (w < 1024) return 'tablet';
        return 'desktop';
    };

    const [bp, setBp] = useState<Breakpoint>(getBreakpoint);

    useEffect(() => {
        let timeout: ReturnType<typeof setTimeout>;
        const handle = () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => setBp(getBreakpoint()), 100);
        };
        window.addEventListener('resize', handle);
        return () => { window.removeEventListener('resize', handle); clearTimeout(timeout); };
    }, []);

    return {
        bp,
        isMobile: bp === 'mobile',
        isTablet: bp === 'tablet',
        isDesktop: bp === 'desktop',
        isMobileOrTablet: bp !== 'desktop',
    };
}

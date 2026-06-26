/**
 * AI Arena - GSAP 动画工具库
 * 封装常用动画，供高级版使用
 */
const Animations = {
    /** 检查 GSAP 是否可用 */
    available: typeof gsap !== 'undefined',

    /** 卡片入场动画（3D 翻转） */
    cardEnter(elements, stagger = 0.1) {
        if (!this.available) return;
        gsap.from(elements, {
            duration: 0.6,
            rotationY: 90,
            opacity: 0,
            scale: 0.8,
            stagger: stagger,
            ease: 'back.out(1.7)',
            transformPerspective: 800,
        });
    },

    /** 气泡弹出动画 */
    bubblePop(element) {
        if (!this.available) return;
        gsap.from(element, {
            duration: 0.4,
            scale: 0.5,
            opacity: 0,
            y: 20,
            ease: 'back.out(2)',
        });
    },

    /** 淘汰爆炸效果 */
    deathExplode(element) {
        if (!this.available) return;
        gsap.timeline()
            .to(element, { duration: 0.15, scale: 1.15, filter: 'brightness(2)', ease: 'power2.out' })
            .to(element, { duration: 0.3, scale: 0.95, filter: 'brightness(1.5)', ease: 'power2.in' })
            .to(element, { duration: 0.2, scale: 1, filter: 'brightness(1)', ease: 'power1.out' });
    },

    /** 游戏结束烟花效果 */
    gameOverFireworks(element) {
        if (!this.available) return;
        gsap.from(element, {
            duration: 0.8,
            scale: 0,
            opacity: 0,
            filter: 'brightness(3)',
            ease: 'elastic.out(1, 0.5)',
        });
    },

    /** 发言者高亮脉冲 */
    speakPulse(element) {
        if (!this.available) return;
        gsap.to(element, {
            duration: 0.8,
            boxShadow: '0 0 30px var(--color-primary-glow), 0 0 60px var(--color-primary-glow)',
            scale: 1.1,
            repeat: -1,
            yoyo: true,
            ease: 'sine.inOut',
        });
    },

    /** 停止脉冲 */
    stopPulse(element) {
        if (!this.available) return;
        gsap.killTweensOf(element);
        gsap.to(element, { duration: 0.3, scale: 1, boxShadow: 'none' });
    },

    /** 旁白打字机效果 */
    typewriter(element, text, speed = 50) {
        if (!this.available) return;
        element.textContent = '';
        const chars = text.split('');
        chars.forEach((char, i) => {
            gsap.to(element, {
                duration: 0.01,
                delay: i * (speed / 1000),
                onComplete: () => { element.textContent += char; },
            });
        });
    },

    /** 页面切换动画 */
    pageTransition(outEl, inEl) {
        if (!this.available) return;
        const tl = gsap.timeline();
        tl.to(outEl, { duration: 0.2, opacity: 0, y: -10, ease: 'power2.in' })
          .set(outEl, { className: '-=active' })
          .set(inEl, { className: '+=active', opacity: 0, y: 10 })
          .to(inEl, { duration: 0.3, opacity: 1, y: 0, ease: 'power2.out' });
        return tl;
    },

    /** 导航栏彩虹渐变流动 */
    navbarGlow(element) {
        if (!this.available) return;
        gsap.to(element, {
            duration: 3,
            backgroundPosition: '-200% 0',
            repeat: -1,
            ease: 'none',
        });
    },

    /** 座位卡悬浮效果 */
    seatHover(element) {
        if (!this.available) return;
        element.addEventListener('mouseenter', () => {
            gsap.to(element, { duration: 0.3, y: -5, scale: 1.05, ease: 'power2.out' });
        });
        element.addEventListener('mouseleave', () => {
            gsap.to(element, { duration: 0.3, y: 0, scale: 1, ease: 'power2.out' });
        });
    },
};

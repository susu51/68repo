// Notification sound file - public/notification.mp3 için placeholder
// Browser'ın built-in beep sound'unu kullanacağız veya basit bir Web Audio API tonu
export const playNotificationSound = () => {
  try {
    // Try to play notification.mp3 if exists
    const audio = new Audio('/notification.mp3');
    audio.volume = 0.5;
    audio.play().catch(() => {
      // Fallback: Use Web Audio API for simple beep
      playBeep();
    });
  } catch (error) {
    // Fallback: Use Web Audio API
    playBeep();
  }
};

const playBeep = () => {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800; // Frequency in Hz
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  } catch (error) {
    console.warn('Audio notification failed:', error);
  }
};

export default playNotificationSound;

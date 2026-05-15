import { useEffect, useRef } from 'react';

export function MapView() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    ctx.fillStyle = '#0A0C10';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw grid pattern
    ctx.strokeStyle = 'rgba(245, 166, 35, 0.05)';
    ctx.lineWidth = 1;

    const gridSize = 50;
    for (let x = 0; x < canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }

    for (let y = 0; y < canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Draw hexagon overlay
    const hexRadius = 40;
    const hexHeight = hexRadius * Math.sqrt(3);

    for (let y = 0; y < canvas.height + hexHeight; y += hexHeight * 0.75) {
      for (let x = 0; x < canvas.width + hexRadius * 2; x += hexRadius * 1.5) {
        const offsetX = (y / (hexHeight * 0.75)) % 2 === 0 ? 0 : hexRadius * 0.75;
        drawHexagon(ctx, x + offsetX, y, hexRadius);
      }
    }

    // Draw random "roads" with amber highlight
    ctx.strokeStyle = 'rgba(245, 166, 35, 0.2)';
    ctx.lineWidth = 3;

    for (let i = 0; i < 8; i++) {
      ctx.beginPath();
      ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
      ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
      ctx.stroke();
    }

    // Draw nearby driver dots
    const driverPositions = [
      { x: canvas.width * 0.3, y: canvas.height * 0.4 },
      { x: canvas.width * 0.6, y: canvas.height * 0.3 },
      { x: canvas.width * 0.5, y: canvas.height * 0.7 },
      { x: canvas.width * 0.8, y: canvas.height * 0.5 },
    ];

    driverPositions.forEach(pos => {
      // Outer glow
      const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, 15);
      gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
      gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 15, 0, Math.PI * 2);
      ctx.fill();

      // Car dot
      ctx.fillStyle = '#3B82F6';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });
  }, []);

  function drawHexagon(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      const hx = x + radius * Math.cos(angle);
      const hy = y + radius * Math.sin(angle);
      if (i === 0) {
        ctx.moveTo(hx, hy);
      } else {
        ctx.lineTo(hx, hy);
      }
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(245, 166, 35, 0.03)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  return (
    <div className="absolute inset-0 z-0">
      <canvas ref={canvasRef} className="w-full h-full" />

      {/* User location pin */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
        <div className="relative">
          {/* Pulsing ring animation */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 bg-[#F5A623] rounded-full opacity-20 animate-ping"></div>
          </div>

          {/* Inner glow */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 bg-[#F5A623] rounded-full opacity-30 blur-xl"></div>
          </div>

          {/* Pin marker */}
          <div className="relative bg-[#F5A623] p-3 rounded-full shadow-lg">
            <div className="w-3 h-3 bg-white rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

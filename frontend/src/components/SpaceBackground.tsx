import React, { useRef, useMemo, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial, Sphere } from '@react-three/drei';
import * as THREE from 'three';

// Generate random points in a sphere
function generateSpherePoints(count: number, radius: number): Float32Array {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = radius * Math.cbrt(Math.random());
    
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
  }
  return positions;
}

// Animated star field
function StarField({ count = 5000 }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => generateSpherePoints(count, 50), [count]);
  
  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 30;
      ref.current.rotation.y -= delta / 40;
    }
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#ffffff"
          size={0.08}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </Points>
    </group>
  );
}

// Blue/purple nebula stars
function NebulaStars({ count = 1500 }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => generateSpherePoints(count, 30), [count]);
  
  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x += delta / 50;
      ref.current.rotation.y += delta / 35;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#5E5CE6"
        size={0.12}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        opacity={0.8}
      />
    </Points>
  );
}

// Cyan accent stars
function CyanStars({ count = 800 }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => generateSpherePoints(count, 25), [count]);
  
  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 60;
      ref.current.rotation.z += delta / 45;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#0A84FF"
        size={0.15}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        opacity={0.7}
      />
    </Points>
  );
}

// Floating orbs with glow effect
function FloatingOrb({ position, color, size = 0.5, speed = 1 }: { 
  position: [number, number, number]; 
  color: string; 
  size?: number;
  speed?: number;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const initialY = position[1];
  
  useFrame((state) => {
    if (ref.current) {
      ref.current.position.y = initialY + Math.sin(state.clock.elapsedTime * speed) * 2;
      ref.current.position.x = position[0] + Math.cos(state.clock.elapsedTime * speed * 0.5) * 1;
    }
  });

  return (
    <Sphere ref={ref} args={[size, 32, 32]} position={position}>
      <meshBasicMaterial color={color} transparent opacity={0.3} />
    </Sphere>
  );
}

// Glowing center orb
function CenterGlow() {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
      ref.current.scale.set(scale, scale, scale);
    }
  });

  return (
    <Sphere ref={ref} args={[8, 64, 64]} position={[0, 0, -20]}>
      <meshBasicMaterial 
        color="#0A84FF" 
        transparent 
        opacity={0.05}
      />
    </Sphere>
  );
}

// Shooting star effect
function ShootingStar() {
  const ref = useRef<THREE.Mesh>(null);
  const speed = useMemo(() => Math.random() * 0.5 + 0.3, []);
  const delay = useMemo(() => Math.random() * 10, []);
  
  useFrame((state) => {
    if (ref.current) {
      const time = (state.clock.elapsedTime + delay) * speed;
      const cycle = time % 8;
      
      if (cycle < 2) {
        ref.current.visible = true;
        ref.current.position.x = 30 - cycle * 30;
        ref.current.position.y = 20 - cycle * 15;
        ref.current.position.z = -10;
        ref.current.scale.setScalar(1 - cycle / 2);
      } else {
        ref.current.visible = false;
      }
    }
  });

  return (
    <Sphere ref={ref} args={[0.1, 8, 8]} position={[30, 20, -10]}>
      <meshBasicMaterial color="#ffffff" />
    </Sphere>
  );
}

// Main scene component
function Scene() {
  return (
    <>
      {/* Ambient atmosphere */}
      <fog attach="fog" args={['#000011', 30, 80]} />
      
      {/* Star layers */}
      <StarField count={4000} />
      <NebulaStars count={1200} />
      <CyanStars count={600} />
      
      {/* Center glow effect */}
      <CenterGlow />
      
      {/* Floating orbs */}
      <FloatingOrb position={[-15, 5, -15]} color="#BF5AF2" size={1.5} speed={0.8} />
      <FloatingOrb position={[12, -8, -12]} color="#0A84FF" size={1.2} speed={1.2} />
      <FloatingOrb position={[8, 10, -18]} color="#5E5CE6" size={1} speed={0.6} />
      <FloatingOrb position={[-10, -5, -10]} color="#32D74B" size={0.8} speed={1} />
      
      {/* Shooting stars */}
      <ShootingStar />
      <ShootingStar />
      <ShootingStar />
    </>
  );
}

// Main SpaceBackground component
const SpaceBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      {/* Gradient overlay for depth */}
      <div 
        className="absolute inset-0 z-10 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse at 20% 20%, rgba(94, 92, 230, 0.15) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(10, 132, 255, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(191, 90, 242, 0.08) 0%, transparent 60%)
          `
        }}
      />
      
      {/* Three.js Canvas */}
      <Canvas
        camera={{ position: [0, 0, 20], fov: 60 }}
        style={{ background: 'transparent' }}
        gl={{ 
          antialias: true, 
          alpha: true,
          powerPreference: 'high-performance'
        }}
        dpr={[1, 1.5]} // Limit device pixel ratio for performance
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
      
      {/* Bottom gradient fade */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-40 z-10 pointer-events-none"
        style={{
          background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%)'
        }}
      />
    </div>
  );
};

export default SpaceBackground;

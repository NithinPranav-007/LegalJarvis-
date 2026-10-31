import React, { useEffect, useRef } from "react";
import * as THREE from "three";

interface Props {
  className?: string;
  interactive?: boolean;
}

export const SupremeCourt3DCanvas: React.FC<Props> = ({
  className = "w-60 h-40",
  interactive = true,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    let width = container.clientWidth || 240;
    let height = container.clientHeight || 160;

    // 1. Scene & Architectural Elevation Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
    camera.position.set(0, 0.35, 4.2);
    camera.lookAt(0, 0.22, 0);

    // 2. WebGL Renderer with Alpha & Antialiasing
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // 3. Crisp High-Contrast Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.35);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 2.8);
    sunLight.position.set(4, 7, 5);
    sunLight.castShadow = true;
    scene.add(sunLight);

    const softFill = new THREE.DirectionalLight(0xe0f2fe, 1.0);
    softFill.position.set(-4, 3, 2);
    scene.add(softFill);

    const emeraldRimLight = new THREE.PointLight(0x10b981, 1.8, 8);
    emeraldRimLight.position.set(-2.5, 0.5, 2.5);
    scene.add(emeraldRimLight);

    // 4. Clean Architectural Materials
    const baseStone = new THREE.MeshStandardMaterial({
      color: 0xd8c8b4, // Sandstone foundation
      roughness: 0.4,
      metalness: 0.05,
    });

    const facadeWhite = new THREE.MeshStandardMaterial({
      color: 0xfcfbf9, // Pure Delhi imperial sandstone cream
      roughness: 0.25,
      metalness: 0.08,
    });

    const pillarMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff, // Bright white fluted colonnade columns
      roughness: 0.2,
      metalness: 0.1,
    });

    const trimDark = new THREE.MeshStandardMaterial({
      color: 0x1f2e27, // Forest green trim
      roughness: 0.3,
      metalness: 0.2,
    });

    const domePatinaGreen = new THREE.MeshStandardMaterial({
      color: 0x3d6b4f, // Iconic Supreme Court patina green dome
      roughness: 0.3,
      metalness: 0.25,
    });

    const brassGold = new THREE.MeshStandardMaterial({
      color: 0xd4af37, // Polished brass gold
      roughness: 0.15,
      metalness: 0.85,
    });

    // 5. 3D Architectural Model of Supreme Court of India
    const courtGroup = new THREE.Group();

    // Symmetrical Steps Plinth
    const plinth1 = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.1, 1.6), baseStone);
    plinth1.position.y = -0.65;
    courtGroup.add(plinth1);

    const plinth2 = new THREE.Mesh(new THREE.BoxGeometry(3.3, 0.1, 1.4), baseStone);
    plinth2.position.y = -0.55;
    courtGroup.add(plinth2);

    const plinth3 = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.1, 1.2), trimDark);
    plinth3.position.y = -0.45;
    courtGroup.add(plinth3);

    // Central Hall Facade
    const centralWall = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.72, 0.9), facadeWhite);
    centralWall.position.y = -0.06;
    courtGroup.add(centralWall);

    // Colonnade Pillars across front
    const pillarGeo = new THREE.CylinderGeometry(0.045, 0.045, 0.72, 16);
    const pillarPositions = [-0.95, -0.68, -0.41, -0.14, 0.14, 0.41, 0.68, 0.95];
    pillarPositions.forEach((x) => {
      const col = new THREE.Mesh(pillarGeo, pillarMaterial);
      col.position.set(x, -0.06, 0.48);
      col.castShadow = true;
      courtGroup.add(col);
    });

    // Entablature (Beam above pillars)
    const entablature = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.1, 1.05), trimDark);
    entablature.position.y = 0.34;
    courtGroup.add(entablature);

    // Triangular Pediment Gable
    const pedimentShape = new THREE.Shape();
    pedimentShape.moveTo(-1.25, 0);
    pedimentShape.lineTo(0, 0.42);
    pedimentShape.lineTo(1.25, 0);
    pedimentShape.closePath();

    const extrudeSettings = { depth: 0.14, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: 0.02, bevelThickness: 0.02 };
    const pedimentGeo = new THREE.ExtrudeGeometry(pedimentShape, extrudeSettings);
    const pedimentMesh = new THREE.Mesh(pedimentGeo, facadeWhite);
    pedimentMesh.position.set(0, 0.39, 0.42);
    courtGroup.add(pedimentMesh);

    // Drum (Octagonal/Cylindrical Base for Dome)
    const drumGeo = new THREE.CylinderGeometry(0.62, 0.65, 0.3, 32);
    const drumMesh = new THREE.Mesh(drumGeo, trimDark);
    drumMesh.position.y = 0.54;
    courtGroup.add(drumMesh);

    // Supreme Court Hemispherical Dome
    const domeGeo = new THREE.SphereGeometry(0.62, 32, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const domeMesh = new THREE.Mesh(domeGeo, domePatinaGreen);
    domeMesh.position.y = 0.69;
    courtGroup.add(domeMesh);

    // Golden Spire / Finial
    const spireGeo = new THREE.CylinderGeometry(0.015, 0.025, 0.38, 16);
    const spireMesh = new THREE.Mesh(spireGeo, brassGold);
    spireMesh.position.y = 1.34;
    courtGroup.add(spireMesh);

    // Tricolor Indian Flag atop
    const flagGeo = new THREE.BoxGeometry(0.22, 0.12, 0.01);
    const flagMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.2 });
    const flagMesh = new THREE.Mesh(flagGeo, flagMat);
    flagMesh.position.set(0.12, 1.48, 0);
    courtGroup.add(flagMesh);

    // 6. Floating 3D Golden Scales of Justice
    const scalesGroup = new THREE.Group();
    scalesGroup.position.set(1.3, 0.65, 0.3);

    const rodMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 0.65, 16), brassGold);
    scalesGroup.add(rodMesh);

    const pivotSphere = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 16), brassGold);
    pivotSphere.position.y = 0.3;
    scalesGroup.add(pivotSphere);

    const beamGroup = new THREE.Group();
    beamGroup.position.y = 0.3;
    const beamMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.78, 16), brassGold);
    beamMesh.rotation.z = Math.PI / 2;
    beamGroup.add(beamMesh);

    // Left pan
    const chainLeft = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.22, 8), brassGold);
    chainLeft.position.set(-0.36, -0.11, 0);
    beamGroup.add(chainLeft);

    const panGeo = new THREE.SphereGeometry(0.11, 16, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
    const panLeft = new THREE.Mesh(panGeo, brassGold);
    panLeft.position.set(-0.36, -0.22, 0);
    panLeft.rotation.x = Math.PI;
    beamGroup.add(panLeft);

    // Right pan
    const chainRight = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.22, 8), brassGold);
    chainRight.position.set(0.36, -0.11, 0);
    beamGroup.add(chainRight);

    const panRight = new THREE.Mesh(panGeo, brassGold);
    panRight.position.set(0.36, -0.22, 0);
    panRight.rotation.x = Math.PI;
    beamGroup.add(panRight);

    scalesGroup.add(beamGroup);
    courtGroup.add(scalesGroup);

    // 7. Citation Sparkles
    const particlesCount = 20;
    const particleGeo = new THREE.SphereGeometry(0.028, 8, 8);
    const particlesGroup = new THREE.Group();
    const particleData: Array<{ mesh: THREE.Mesh; speed: number; angle: number; radius: number; yBase: number }> = [];

    for (let i = 0; i < particlesCount; i++) {
      const isEmerald = i % 2 === 0;
      const pMesh = new THREE.Mesh(
        particleGeo,
        new THREE.MeshBasicMaterial({
          color: isEmerald ? 0x10b981 : 0xf59e0b,
          transparent: true,
          opacity: 0.8,
        })
      );
      const angle = (i / particlesCount) * Math.PI * 2;
      const radius = 1.6 + Math.random() * 0.7;
      const yBase = -0.3 + Math.random() * 1.6;
      pMesh.position.set(Math.cos(angle) * radius, yBase, Math.sin(angle) * radius);
      particlesGroup.add(pMesh);
      particleData.push({
        mesh: pMesh,
        speed: 0.006 + Math.random() * 0.006,
        angle,
        radius,
        yBase,
      });
    }
    courtGroup.add(particlesGroup);

    scene.add(courtGroup);

    // 8. Subtle Upright Orientation & Mouse Tracking
    let targetRotationX = 0.02;
    let targetRotationY = -0.06;
    let currentRotationX = targetRotationX;
    let currentRotationY = targetRotationY;

    const handleMouseMove = (event: MouseEvent) => {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      targetRotationY = -0.06 + x * 0.35;
      targetRotationX = 0.02 + y * 0.2;
    };

    if (interactive) {
      window.addEventListener("mousemove", handleMouseMove);
    }

    // 9. Animation Loop
    let animationId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      currentRotationX += (targetRotationX - currentRotationX) * 0.05;
      currentRotationY += (targetRotationY - currentRotationY) * 0.05;

      courtGroup.rotation.x = currentRotationX;
      courtGroup.rotation.y = currentRotationY;

      // Gentle floating bob
      courtGroup.position.y = Math.sin(elapsedTime * 1.2) * 0.03;

      // Gentle scales swing
      beamGroup.rotation.z = Math.sin(elapsedTime * 1.8) * 0.1;

      // Flag flutter
      flagMesh.rotation.y = Math.sin(elapsedTime * 4.0) * 0.15;

      // Orbit particles
      particleData.forEach((p) => {
        p.angle += p.speed;
        p.mesh.position.x = Math.cos(p.angle) * p.radius;
        p.mesh.position.z = Math.sin(p.angle) * p.radius;
        p.mesh.position.y = p.yBase + Math.sin(elapsedTime * 2.0 + p.angle) * 0.06;
      });

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      if (newWidth > 0 && newHeight > 0) {
        camera.aspect = newWidth / newHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(newWidth, newHeight);
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationId);
      if (interactive) {
        window.removeEventListener("mousemove", handleMouseMove);
      }
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [interactive]);

  return (
    <div
      ref={mountRef}
      className={`relative transition-transform shrink-0 ${className}`}
      title="3D Supreme Court of India Architecture"
      aria-label="3D Supreme Court of India Architecture"
    />
  );
};

export default SupremeCourt3DCanvas;

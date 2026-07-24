// Kestrel 3D hero — scroll-driven flight sequence.
// Beats: take off, find the line, perch, harvest, deliver to the ground station.
// Procedural Three.js scene: PBR materials, ACES tone mapping, dusk lighting.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const container = document.getElementById('drone3d');
if (container && window.WebGLRenderingContext) {
    init(container);
}

function clamp01(v) { return Math.min(1, Math.max(0, v)); }
function smooth(v) { v = clamp01(v); return v * v * (3 - 2 * v); }
function seg(p, a, b) { return smooth((p - a) / (b - a)); }

function init(container) {
    const BRAND = 0xff5a1f;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const heroWrap = document.getElementById('hero');
    const heroText = document.querySelector('.hero-text');
    const stepEl = document.getElementById('heroStep');

    // The scroll runway: only when 3D is actually running
    if (!reduced && heroWrap) heroWrap.style.height = '420vh';

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b0d13);
    scene.fog = new THREE.Fog(0x0b0d13, 45, 150);

    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    const camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.1, 300);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableZoom = false;
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.autoRotateSpeed = 0.55;
    controls.minPolarAngle = 0.9;
    controls.maxPolarAngle = 1.52;
    controls.enabled = false; // scripted camera until the sequence completes
    if (window.matchMedia('(pointer: coarse)').matches) controls.enableRotate = false;

    // ── Lights ─────────────────────────────────────────────────────────────
    const sun = new THREE.DirectionalLight(0xff7a3c, 2.6);
    sun.position.set(-38, 7, -20);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -25; sun.shadow.camera.right = 25;
    sun.shadow.camera.top = 25; sun.shadow.camera.bottom = -25;
    scene.add(sun);
    scene.add(new THREE.HemisphereLight(0x2c3a58, 0x0d0d0f, 0.95));
    const fill = new THREE.DirectionalLight(0x9fb2d8, 0.85);
    fill.position.set(22, 14, 20);
    scene.add(fill);
    const droneKey = new THREE.PointLight(0xcfd8ea, 3.2, 12);
    scene.add(droneKey);
    const maglineGlow = new THREE.PointLight(BRAND, 0, 7);
    scene.add(maglineGlow);

    // ── Materials ──────────────────────────────────────────────────────────
    const matDark   = new THREE.MeshStandardMaterial({ color: 0x1b1d22, roughness: 0.45, metalness: 0.75 });
    const matSteel  = new THREE.MeshStandardMaterial({ color: 0x3a3f47, roughness: 0.5, metalness: 0.9 });
    const matWire   = new THREE.MeshStandardMaterial({ color: 0x2c2f36, roughness: 0.35, metalness: 0.95 });
    const matBody   = new THREE.MeshStandardMaterial({ color: 0x15161a, roughness: 0.32, metalness: 0.6 });
    const matBrand  = new THREE.MeshStandardMaterial({ color: 0x1a1108, roughness: 0.4, metalness: 0.3, emissive: BRAND, emissiveIntensity: 0.15 });
    const matRotor  = new THREE.MeshStandardMaterial({ color: 0x111216, roughness: 0.3, metalness: 0.4, transparent: true, opacity: 0.32, side: THREE.DoubleSide });
    const matGround = new THREE.MeshStandardMaterial({ color: 0x0e0f11, roughness: 1.0, metalness: 0.0 });
    const matArmy   = new THREE.MeshStandardMaterial({ color: 0x2a2e24, roughness: 0.7, metalness: 0.25 });
    const matPulse  = new THREE.MeshBasicMaterial({ color: BRAND });

    // ── Ground ─────────────────────────────────────────────────────────────
    const ground = new THREE.Mesh(new THREE.CircleGeometry(140, 48), matGround);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    // ── Pylons ─────────────────────────────────────────────────────────────
    function pylon(x) {
        const g = new THREE.Group();
        const leg = (dx) => {
            const m = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.14, 11, 8), matSteel);
            m.position.set(dx, 5.5, 0);
            m.rotation.z = dx > 0 ? -0.06 : 0.06;
            m.castShadow = true;
            return m;
        };
        g.add(leg(-0.55), leg(0.55));
        const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 3.4, 8), matSteel);
        arm.rotation.z = Math.PI / 2;
        arm.position.y = 10.4;
        g.add(arm);
        for (const bz of [-1.35, 1.35]) {
            const ins = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.55, 8), matDark);
            ins.position.set(bz, 10.05, 0);
            g.add(ins);
        }
        for (let i = 0; i < 4; i++) {
            const brace = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 1.35, 6), matSteel);
            brace.position.set(0, 2 + i * 2.3, 0);
            brace.rotation.z = i % 2 ? 0.75 : -0.75;
            g.add(brace);
        }
        g.position.x = x;
        scene.add(g);
    }
    pylon(-30); pylon(30);

    // ── Wire ───────────────────────────────────────────────────────────────
    const wireCurve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-28.6, 9.78, 0),
        new THREE.Vector3(0, 8.0, 0),
        new THREE.Vector3(28.6, 9.78, 0),
    ]);
    const wire = new THREE.Mesh(new THREE.TubeGeometry(wireCurve, 80, 0.035, 8), matWire);
    wire.castShadow = true;
    scene.add(wire);

    // ── Kestrel (Magline attached, so the whole unit flies) ────────────────
    const drone = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.36, 0.95), matBody);
    body.castShadow = true;
    drone.add(body);
    const canopy = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.16, 0.6), matDark);
    canopy.position.y = 0.26;
    drone.add(canopy);

    const rotors = [];
    for (const [ax, az] of [[-1.15, -0.95], [1.15, -0.95], [-1.15, 0.95], [1.15, 0.95]]) {
        const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, Math.hypot(ax, az) - 0.3, 8), matBody);
        arm.rotation.z = Math.PI / 2;
        arm.rotation.y = -Math.atan2(az, ax);
        arm.position.set(ax * 0.5, 0.05, az * 0.5);
        drone.add(arm);
        const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 0.22, 10), matDark);
        hub.position.set(ax, 0.14, az);
        drone.add(hub);
        const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 0.015, 24), matRotor);
        disc.position.set(ax, 0.26, az);
        drone.add(disc);
        rotors.push(disc);
    }
    for (const lx of [-0.42, 0.42]) {
        const legm = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.5, 0.14), matBody);
        legm.position.set(lx, -0.42, 0);
        drone.add(legm);
    }
    // Magline under the body
    const magline = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.4, 0.45), matBody);
    magline.position.set(0, -0.64, 0);
    magline.castShadow = true;
    drone.add(magline);
    for (const rx of [-0.32, 0.32]) {
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.21, 0.035, 10, 28), matBrand);
        ring.position.set(rx, -0.62, 0);
        ring.rotation.y = Math.PI / 2;
        drone.add(ring);
    }
    scene.add(drone);

    // ── Ground station + vehicle ───────────────────────────────────────────
    const stationPos = new THREE.Vector3(2.6, 0.55, 5.6);
    const station = new THREE.Mesh(new THREE.BoxGeometry(1.7, 1.1, 1.05), matArmy);
    station.position.copy(stationPos);
    station.castShadow = true;
    scene.add(station);
    const slit = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.06, 0.02), matBrand);
    slit.position.set(stationPos.x, 0.85, stationPos.z + 0.54);
    scene.add(slit);

    const vehicle = new THREE.Group();
    const hull = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.75, 1.5), matArmy);
    hull.position.y = 0.85;
    hull.castShadow = true;
    vehicle.add(hull);
    const turret = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.35, 0.9), matDark);
    turret.position.y = 1.4;
    vehicle.add(turret);
    for (const [wx, wz] of [[-0.95, -0.85], [0.95, -0.85], [-0.95, 0.85], [0.95, 0.85]]) {
        const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 0.28, 16), matDark);
        wheel.rotation.x = Math.PI / 2;
        wheel.position.set(wx, 0.38, wz);
        vehicle.add(wheel);
    }
    vehicle.position.set(7.6, 0, 7.2);
    vehicle.rotation.y = -0.5;
    scene.add(vehicle);

    // ── Tether: live geometry from station to wherever the drone is ────────
    const tether = new THREE.Mesh(undefined, matDark);
    scene.add(tether);
    let tetherCurve = null;
    function updateTether() {
        const anchor = new THREE.Vector3(stationPos.x, 1.1, stationPos.z);
        const tip = drone.position.clone().add(new THREE.Vector3(0, -0.85, 0));
        const mid = anchor.clone().lerp(tip, 0.5);
        mid.y = Math.min(anchor.y, tip.y) + (tip.distanceTo(anchor) * 0.08);
        tetherCurve = new THREE.QuadraticBezierCurve3(anchor, mid, tip);
        if (tether.geometry) tether.geometry.dispose();
        tether.geometry = new THREE.TubeGeometry(tetherCurve, 24, 0.02, 8);
    }

    // Power cable station → vehicle
    const busCurve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(stationPos.x + 0.85, 0.35, stationPos.z),
        new THREE.Vector3(5, 0.12, 6.6),
        new THREE.Vector3(6.7, 0.45, 7.0),
    );
    scene.add(new THREE.Mesh(new THREE.TubeGeometry(busCurve, 24, 0.02, 8), matDark));

    // ── Energy pulses ──────────────────────────────────────────────────────
    const wirePulses = [], deliverPulses = [];
    function addPulse(list, curveRef, count, speed, size) {
        for (let i = 0; i < count; i++) {
            const m = new THREE.Mesh(new THREE.SphereGeometry(size, 8, 8), matPulse);
            scene.add(m);
            list.push({ m, curveRef, t: i / count, speed });
        }
    }
    const wireL = new THREE.CatmullRomCurve3([new THREE.Vector3(-28.6, 9.78, 0), new THREE.Vector3(-14, 8.6, 0), new THREE.Vector3(-0.5, 8.0, 0)]);
    const wireR = new THREE.CatmullRomCurve3([new THREE.Vector3(28.6, 9.78, 0), new THREE.Vector3(14, 8.6, 0), new THREE.Vector3(0.5, 8.0, 0)]);
    addPulse(wirePulses, () => wireL, 4, 0.12, 0.075);
    addPulse(wirePulses, () => wireR, 4, 0.12, 0.075);
    addPulse(deliverPulses, () => tetherCurve, 3, 0.25, 0.06);
    addPulse(deliverPulses, () => busCurve, 2, 0.4, 0.05);

    // ── Flight path: ground → climb → approach → settle on the wire ───────
    const flightPath = new THREE.CatmullRomCurve3([
        new THREE.Vector3(5.2, 0.62, 3.2),
        new THREE.Vector3(5.3, 5.2, 3.0),
        new THREE.Vector3(3.2, 10.8, 1.2),
        new THREE.Vector3(0.9, 9.9, 0.15),
        new THREE.Vector3(0, 8.62, 0),
    ]);

    // ── Scroll progress ────────────────────────────────────────────────────
    function progress() {
        if (reduced || !heroWrap) return 1;
        const runway = heroWrap.offsetHeight - window.innerHeight;
        if (runway <= 10) return 1;
        return clamp01(-heroWrap.getBoundingClientRect().top / runway);
    }

    const STEPS = [
        [0.00, 'Scroll'],
        [0.06, '01 · Take off'],
        [0.32, '02 · Find the line'],
        [0.58, '03 · Perch'],
        [0.72, '04 · Harvest'],
        [0.86, '05 · Deliver to the ground station'],
    ];

    const camA = new THREE.Vector3(9.0, 1.9, 11.0);
    const camB = new THREE.Vector3(11.5, 7.5, 13.5);
    const camC = new THREE.Vector3(10.5, 9.5, 14.5);
    const endTarget = new THREE.Vector3(-4.5, 6.8, 0.8);
    const tmpTarget = new THREE.Vector3();
    const tmpPos = new THREE.Vector3();

    let visible = true;
    new IntersectionObserver((es) => { visible = es[0].isIntersecting; }, { threshold: 0.01 }).observe(container);

    const clock = new THREE.Clock();
    renderer.setAnimationLoop(() => {
        if (!visible) return;
        const dt = clock.getDelta();
        const p = progress();

        // Drone along the flight path
        const ft = seg(p, 0.06, 0.70);
        drone.position.copy(flightPath.getPointAt(ft));
        // Lean into the direction of travel while flying
        if (ft > 0.01 && ft < 0.99) {
            const ahead = flightPath.getPointAt(Math.min(1, ft + 0.03));
            drone.rotation.z = clamp01((ahead.x - drone.position.x) * -0.5) * 0.25 - 0.05;
            drone.rotation.y = 0.3 * Math.sin(ft * Math.PI);
        } else {
            drone.rotation.z *= 0.9;
            drone.rotation.y *= 0.9;
        }
        // Perched idle breathing
        if (p > 0.72) drone.position.y += Math.sin(clock.elapsedTime * 1.4) * 0.012;

        // Rotors: idle, spin up, fly, spin down after perch
        const spin = 0.12 + seg(p, 0.02, 0.12) * (1 - seg(p, 0.62, 0.76));
        for (const r of rotors) r.rotation.y += dt * 44 * spin;

        // Tether follows the drone
        updateTether();

        // Harvest: Magline wakes up after perch
        const harvest = seg(p, 0.72, 0.86);
        matBrand.emissiveIntensity = 0.15 + harvest * 1.9;
        maglineGlow.intensity = harvest * (5.4 + Math.sin(clock.elapsedTime * 3) * 1.2);
        maglineGlow.position.copy(drone.position).add(new THREE.Vector3(0, -0.6, 0));
        droneKey.position.copy(drone.position).add(new THREE.Vector3(3, 2.5, 3));

        // Wire pulses always run; delivery pulses only after harvest
        for (const q of wirePulses) {
            q.t = (q.t + dt * q.speed) % 1;
            q.m.position.copy(q.curveRef().getPointAt(q.t));
        }
        const delivering = p > 0.86;
        for (const q of deliverPulses) {
            q.m.visible = delivering;
            if (delivering && q.curveRef()) {
                q.t = (q.t + dt * q.speed) % 1;
                q.m.position.copy(q.curveRef().getPointAt(q.t));
            }
        }

        // Camera: low chase shot, rising to the wide system view
        if (p < 0.97) {
            controls.enabled = false;
            controls.autoRotate = false;
            const c1 = seg(p, 0, 0.55), c2 = seg(p, 0.55, 1);
            tmpPos.lerpVectors(camA, camB, c1).lerp(camC, c2);
            camera.position.copy(tmpPos);
            tmpTarget.copy(drone.position).lerp(endTarget, seg(p, 0.7, 1));
            camera.lookAt(tmpTarget);
        } else {
            if (!controls.enabled) {
                controls.target.copy(endTarget);
                controls.enabled = true;
                controls.autoRotate = true;
            }
            controls.update();
        }

        // Hero text fades out as flight begins; step label narrates
        if (heroText) {
            const op = 1 - seg(p, 0.02, 0.16);
            heroText.style.opacity = op;
            heroText.style.pointerEvents = op < 0.3 ? 'none' : '';
        }
        if (stepEl) {
            let label = STEPS[0][1];
            for (const [at, txt] of STEPS) if (p >= at) label = txt;
            if (stepEl.textContent !== label) stepEl.textContent = label;
            stepEl.style.opacity = p >= 0.06 && p < 0.99 ? 1 : (p < 0.06 ? 0.6 : 0);
        }

        renderer.render(scene, camera);
    });

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}

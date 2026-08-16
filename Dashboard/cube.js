/* ========================================================= FLICK — AUTOMATIC MOVIE CUBE ========================================================= */
/* ========================================================= CUBE CSS ========================================================= */
const cubeCSS = `
.cube-viewport {
  width: 400px;
  height: 400px;
  perspective: 1100px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: cubeFloat 5s ease-in-out infinite;
}
@keyframes cubeFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-12px); }
}
#cubeScene {
  width: 0;
  height: 0;
  position: relative;
  transform-style: preserve-3d;
  transform: rotateX(-20deg) rotateY(25deg);
  cursor: grab;
}
#cubeScene:active {
  cursor: grabbing;
}
.cubie {
  position: absolute;
  width: 66px;
  height: 66px;
  margin: -33px 0 0 -33px;
  transform-style: preserve-3d;
  will-change: transform;
}
.cubie-face {
  position: absolute;
  width: 66px;
  height: 66px;
  border: 1px solid rgba(0, 0, 0, 0.85);
  border-radius: 4px;
  backface-visibility: visible;
  background-size: 198px 198px;
  background-repeat: no-repeat;
  background-color: #080808;
  box-shadow: inset 0 0 2px rgba(255, 255, 255, 0.1);
}
.cube-ui {
  text-align: center;
  margin-top: 20px;
}
.cube-status {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: var(--accent, #6366f1);
  margin-bottom: 12px;
}
.cbtn {
  padding: 8px 18px;
  background: var(--bg-card, #161621);
  border: 1px solid var(--border-color, rgba(255,255,255,.08));
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  margin: 0 5px;
}
.cbtn:hover {
  border-color: var(--accent, #6366f1);
  color: var(--accent, #6366f1);
}
.cbtn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
@media (max-width: 900px) {
  .cube-viewport {
    width: 320px;
    height: 320px;
  }
}
@media (max-width: 500px) {
  .cube-viewport {
    width: 260px;
    height: 260px;
  }
}
`;

/* Inject cube CSS */
const cubeStyle = document.createElement("style");
cubeStyle.textContent = cubeCSS;
document.head.appendChild(cubeStyle);

/* ========================================================= BASIC SETUP ========================================================= */
const STEP_PX = 66;
const HALF_PX = 33;
const cubeScene = document.getElementById("cubeScene");
const cubeStatus = document.getElementById("cubeStatus");
const btnScramble = document.getElementById("btnScramble");
const btnSolve = document.getElementById("btnSolve");
let cubies = [];
let history = [];
let busy = false;
let autoRunning = false;

/* ========================================================= MOVIE IMAGES ========================================================= */
const frontImages = [
  "img1.jpg",
  "img3.webp",
  "2.jpeg",
  "img4.jpg",
  "img6.jpg",
  "img9.jpg",
  "dark-knight.jpg",
  
];
let currentImageIndex = 0;

/* ========================================================= OTHER CUBE FACES ========================================================= */
const faceImages = {
  front: frontImages[0],
  back: "img3.webp",
  right: "2.jpeg",
  left: "img4.jpg",
  top: "img9.jpg",
  bottom: "dark-knight.jpg",
};

/* ========================================================= FACE DEFINITIONS ========================================================= */
const FACE_DEFINITIONS = [
  { name: "front", transform: `translateZ(${HALF_PX}px)`, normal: [0, 0, 1] },
  { name: "back", transform: `rotateY(180deg) translateZ(${HALF_PX}px)`, normal: [0, 0, -1] },
  { name: "right", transform: `rotateY(90deg) translateZ(${HALF_PX}px)`, normal: [1, 0, 0] },
  { name: "left", transform: `rotateY(-90deg) translateZ(${HALF_PX}px)`, normal: [-1, 0, 0] },
  { name: "top", transform: `rotateX(90deg) translateZ(${HALF_PX}px)`, normal: [0, 1, 0] },
  { name: "bottom", transform: `rotateX(-90deg) translateZ(${HALF_PX}px)`, normal: [0, -1, 0] },
];

/* ========================================================= CREATE CUBIE ========================================================= */
function makeCubie(lx, ly, lz) {
  const el = document.createElement("div");
  el.className = "cubie";
  
  FACE_DEFINITIONS.forEach((faceData, index) => {
    const face = document.createElement("div");
    face.className = "cubie-face";
    face.dataset.face = faceData.name;
    face.dataset.index = index;
    face.style.transform = faceData.transform;
    
    let active = false;
    if (faceData.name === "front" && lz === 1) active = true;
    if (faceData.name === "back" && lz === -1) active = true;
    if (faceData.name === "right" && lx === 1) active = true;
    if (faceData.name === "left" && lx === -1) active = true;
    if (faceData.name === "top" && ly === 1) active = true;
    if (faceData.name === "bottom" && ly === -1) active = true;

    if (active) {
      const position = getImagePosition(faceData.name, lx, ly, lz);
      face.style.backgroundImage = `url("${getFaceImage(faceData.name)}")`;
      face.style.backgroundPosition = position;
    } else {
      face.style.backgroundColor = "#050505";
    }
    el.appendChild(face);
  });

  const matrix = new DOMMatrix().translate(
    lx * STEP_PX,
    -ly * STEP_PX,
    lz * STEP_PX
  );
  el.style.transform = matrix.toString();
  return { el, m: matrix };
}

/* ========================================================= IMAGE HELPERS ========================================================= */
function getFaceImage(faceName) {
  if (faceName === "front") {
    return frontImages[currentImageIndex];
  }
  return faceImages[faceName];
}

function getImagePosition(faceName, lx, ly, lz) {
  const ix = lx + 1;
  const iy = 1 - ly;
  const iz = lz + 1;
  let x = 0;
  let y = 0;
  
  if (faceName === "front") { x = ix; y = iy; }
  else if (faceName === "back") { x = 2 - ix; y = iy; }
  else if (faceName === "right") { x = 2 - iz; y = iy; }
  else if (faceName === "left") { x = iz; y = iy; }
  else if (faceName === "top") { x = ix; y = iz; }
  else if (faceName === "bottom") { x = ix; y = 2 - iz; }
  
  return `-${x * STEP_PX}px -${y * STEP_PX}px`;
}

/* ========================================================= BUILD CUBE ========================================================= */
function buildCube() {
  if (!cubeScene) return;
  cubeScene.innerHTML = "";
  cubies = [];
  history = [];
  for (let y = 1; y >= -1; y--) {
    for (let x = -1; x <= 1; x++) {
      for (let z = 1; z >= -1; z--) {
        const cubie = makeCubie(x, y, z);
        cubeScene.appendChild(cubie.el);
        cubies.push(cubie);
      }
    }
  }
}

/* ========================================================= ROTATE LAYER - RUBIK'S TACTILE VERSION ========================================================= */
function rotateLayer(axis, slice, angle, duration = 240) {
  return new Promise((resolve) => {
    const layer = cubies.filter((cubie) => {
      const x = Math.round(cubie.m.m41 / STEP_PX);
      const y = Math.round(-cubie.m.m42 / STEP_PX);
      const z = Math.round(cubie.m.m43 / STEP_PX);
      const position = axis === "x" ? x : axis === "y" ? y : z;
      return position === slice;
    });

    const pivot = document.createElement("div");
    pivot.style.cssText = `
      position: absolute;
      top: 0; left: 0;
      width: 0; height: 0;
      transform-style: preserve-3d;
      pointer-events: none;
    `;
    cubeScene.appendChild(pivot);

    layer.forEach((cubie) => {
      const currentTransform = cubie.el.style.transform;
      cubie.el.remove();
      pivot.appendChild(cubie.el);
      cubie.el.style.transform = currentTransform;
      cubie.el.style.transition = 'none';
    });

    pivot.getBoundingClientRect();

    const rotation = `rotate${axis.toUpperCase()}(${angle}deg)`;
    // Quintic deceleration curve for realistic friction + snap
    pivot.style.transition = `transform ${duration}ms cubic-bezier(0.25, 1, 0.5, 1)`;

    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;

      const rotationMatrix = new DOMMatrix(`rotate${axis.toUpperCase()}(${angle}deg)`);

      layer.forEach((cubie) => {
        cubie.m = rotationMatrix.multiply(cubie.m);
        // Clean snap positions to eliminate floating point accuracy loss
        cubie.m.m41 = Math.round(cubie.m.m41);
        cubie.m.m42 = Math.round(cubie.m.m42);
        cubie.m.m43 = Math.round(cubie.m.m43);

        const el = cubie.el;
        el.remove();
        cubeScene.appendChild(el);
        el.style.transform = cubie.m.toString();
        el.style.transition = 'none';
      });

      pivot.remove();
      resolve();
    };

    pivot.addEventListener("transitionend", finish, { once: true });

    requestAnimationFrame(() => {
      pivot.style.transform = rotation;
    });

    setTimeout(finish, duration + 60);
  });
}

/* ========================================================= SCRAMBLE MOVES ========================================================= */
const MOVES = [
  { axis: "x", slice: 1, angle: 90 },
  { axis: "x", slice: -1, angle: -90 },
  { axis: "y", slice: 1, angle: 90 },
  { axis: "y", slice: -1, angle: -90 },
  { axis: "z", slice: 1, angle: 90 },
  { axis: "z", slice: -1, angle: -90 },
];

/* ========================================================= RANDOM MOVE ========================================================= */
function getRandomMove(previous) {
  let move;
  do {
    move = MOVES[Math.floor(Math.random() * MOVES.length)];
  } while (
    previous &&
    move.axis === previous.axis &&
    move.slice === previous.slice
  );
  return { ...move };
}

/* ========================================================= SCRAMBLE ========================================================= */
async function scrambleCube(moveCount = 10) {
  if (busy) return;
  busy = true;
  setStatus("Scrambling...");
  disableButtons(true);
  history = [];
  let previous = null;
  for (let i = 0; i < moveCount; i++) {
    const move = getRandomMove(previous);
    previous = move;
    history.push({ axis: move.axis, slice: move.slice, angle: move.angle });
    await rotateLayer(move.axis, move.slice, move.angle, 180);
    await sleep(25);
  }
  setStatus("Status: Scrambled");
  busy = false;
  disableButtons(false);
}

/* ========================================================= SOLVE ========================================================= */
async function solveCube() {
  if (busy || history.length === 0) return;
  busy = true;
  setStatus("Solving...");
  disableButtons(true);
  
  while (history.length > 0) {
    const move = history.pop();
    await rotateLayer(move.axis, move.slice, -move.angle, 220);
    await sleep(30);
  }
  
  setStatus("Status: Solved ✓");
  busy = false;
  disableButtons(false);
}

/* ========================================================= CHANGE FRONT IMAGES ========================================================= */
function changeFrontImage() {
  currentImageIndex = (currentImageIndex + 1) % frontImages.length;
  const frontFaces = document.querySelectorAll('.cubie-face[data-face="front"]');
  frontFaces.forEach((face) => {
    face.style.backgroundImage = `url("${frontImages[currentImageIndex]}")`;
  });
}

/* ========================================================= CONTINUOUS IMAGE ROTATION ========================================================= */
function startImageRotation() {
  setInterval(() => {
    changeFrontImage();
  }, 1800);
}

/* ========================================================= AUTOMATIC SCRAMBLE → SOLVE LOOP ========================================================= */
async function automaticCubeLoop() {
  if (autoRunning) return;
  autoRunning = true;
  await sleep(1500);
  while (autoRunning) {
    await scrambleCube(10);
    await sleep(800);
    await solveCube();
    await sleep(1500);
  }
}

/* ========================================================= STATUS ========================================================= */
function setStatus(text) {
  if (!cubeStatus) return;
  cubeStatus.textContent = text;
}

/* ========================================================= BUTTON CONTROL ========================================================= */
function disableButtons(disabled) {
  if (btnScramble) btnScramble.disabled = disabled;
  if (btnSolve) btnSolve.disabled = disabled;
}

/* ========================================================= SLEEP ========================================================= */
function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

/* ========================================================= MANUAL BUTTONS ========================================================= */
if (btnScramble) {
  btnScramble.addEventListener("click", async () => {
    if (busy) return;
    await scrambleCube(10);
  });
}
if (btnSolve) {
  btnSolve.addEventListener("click", async () => {
    if (busy) return;
    await solveCube();
  });
}

/* ========================================================= START ========================================================= */
if (cubeScene) {
  buildCube();
  startImageRotation();
  automaticCubeLoop();
}
// Initialisation de la scène
const D2R = Math.PI / 180;
const EP = 0.01 // epaisseur de plans
const SDIST = 2
// Le JSON est dans geom

console.log(geom)

const scene = new THREE.Scene();

// Création de la caméra
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 5;

// Création du rendu
const renderer = new THREE.WebGLRenderer();

renderer.setSize(500,500);
document.getElementById('three-container').appendChild(renderer.domElement);
sizeChanged()

const axesHelper = new THREE.AxesHelper(1);  // Taille des axes
// Axe X (rouge) : horizontal, de gauche à droite
// Axe Y (vert) : vertical, de bas en haut
// Axe Z (bleu) : perpendiculaire au plan XY, de l'avant vers l'arrière
scene.add(axesHelper);

// On ajoute le capteur
const geometry = new THREE.BoxGeometry(geom.collector.w, EP, geom.collector.L);
const material = new THREE.MeshBasicMaterial({color: 0x000099, side: THREE.DoubleSide});
const collector = new THREE.Mesh(geometry, material);
collector.position.x = geom.collector.x
collector.position.y = geom.collector.y
scene.add(collector);

// On ajoute les miroirs

// Soleil
const axis = geom.axis*D2R
console.log("axis=", axis)


const a = geom.sun.az * D2R
const h = geom.sun.el * D2R

// Direction du SUD
const south_dir = new THREE.Vector3(Math.cos(axis), 0, Math.sin(-axis)); // Direction de la flèche
south_dir.normalize();

// Direction du Soleil
dx = SDIST * Math.cos(h) * Math.cos(a-axis)
dy = SDIST * Math.sin(h)
dz = SDIST * Math.cos(h) * Math.sin(a-axis)

const sun_dir = new THREE.Vector3(dx, dy, dz); // Direction de la flèche
sun_dir.normalize();


// Direction du SUD (depuis collecteur)
const south_arrow = new THREE.ArrowHelper(south_dir, collector.position, 2, 0xffff00);
scene.add(south_arrow);

// Direction du Soleil (depuis le collecteur)
const sun_arrow = new THREE.ArrowHelper(sun_dir, collector.position, 2, 0xffffff);
scene.add(sun_arrow);


geom.mirrors.pos.forEach(pos => {
    const geometry = new THREE.BoxGeometry(geom.mirrors.w, EP, geom.mirrors.L);
    const material = new THREE.MeshBasicMaterial({color: 0xeeeeee, side: THREE.DoubleSide});
    const mirror = new THREE.Mesh(geometry, material);
    mirror.rotation.z = pos.a * D2R
    mirror.position.x = pos.x
    mirror.position.y = pos.y
    scene.add(mirror);

    const sun_arrow = new THREE.ArrowHelper(sun_dir, mirror.position, 1, 0xffffff);
    scene.add(sun_arrow);

})



//ON centre sur le milieu de la scene
const box = new THREE.Box3().setFromObject(scene);

// Calculer le centre de la boîte englobante
const center = new THREE.Vector3();
box.getCenter(center);

// Centrer la caméra sur le centre de la boîte englobante
//camera.position.set(center.x + cameraDistance, center.y + cameraDistance, center.z + cameraDistance);
camera.lookAt(center);
//controls.target.copy(center);

// Afficher la boîte englobante
//const helper = new THREE.Box3Helper(box, 0xffff00);
//scene.add(helper);


// Création d'un objet géométrique (un cube dans ce cas)
//const geometry = new THREE.BoxGeometry();
//const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
//const cube = new THREE.Mesh(geometry, material);
//scene.add(cube);

// Initialisation des OrbitControls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.25;
controls.enableZoom = true;

// Fonction d'animation
function animate() {
    requestAnimationFrame(animate);
    // Mettre à jour les contrôles
    controls.update();
    // Rendu de la scène
    renderer.render(scene, camera);
}

// Appeler la fonction d'animation
animate();

function sizeChanged() {
    const div = document.getElementById('three-container');
    const width = div.clientWidth;
    const height = div.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

// Adapter le rendu lorsque la taille de la fenêtre change
window.addEventListener('resize', () => {
    sizeChanged();
});

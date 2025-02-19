document.addEventListener("DOMContentLoaded", function() {
    let currentIndex = 0;
    const images = document.querySelectorAll('.carousel img');

    function showNextImage() {
        images[currentIndex].classList.remove('active');
        currentIndex = (currentIndex + 1) % images.length;
        images[currentIndex].classList.add('active');
    }

    setInterval(showNextImage, 3000);
});

// ---------------- GLOBE ANIMATION ----------------
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, 500);
document.getElementById("globe-container").appendChild(renderer.domElement);

// Create Globe
const geometry = new THREE.SphereGeometry(5, 64, 64);
const texture = new THREE.TextureLoader().load('/static/globe.jpg');
const material = new THREE.MeshBasicMaterial({ map: texture });
const globe = new THREE.Mesh(geometry, material);
scene.add(globe);

camera.position.z = 10;

// Locations
const locations = [
    { lat: 37.7749, lon: -122.4194 }, // SF
    { lat: 51.5074, lon: -0.1278 },   // London
    { lat: 35.6895, lon: 139.6917 },  // Tokyo
    { lat: -33.8688, lon: 151.2093 }  // Sydney
];

function latLonToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    return new THREE.Vector3(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
    );
}
/*
// Add Points
const pointMaterial = new THREE.MeshBasicMaterial({ color: 0xff9900 });
locations.forEach(loc => {
    const pointGeo = new THREE.SphereGeometry(0.1, 32, 32);
    const point = new THREE.Mesh(pointGeo, pointMaterial);
    const pos = latLonToVector3(loc.lat, loc.lon, 5.1);
    
    point.position.copy(pos);
    scene.add(point);
    gsap.from(point.position, { duration: 2, x: 0, y: 0, z: 0, ease: "power2.out" });
});
*/
function animate() {
    requestAnimationFrame(animate);
    globe.rotation.y += 0.002;
    renderer.render(scene, camera);
}

animate();

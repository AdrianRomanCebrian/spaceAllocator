// Función para manejar clic en las tarjetas de tarea
function handleClick(taskId, estado, name) {
    // Solo redirigir si el estado no es "EN PROGRESO"
    if (estado !== "EN PROGRESO") {
        window.location.href = '/get_results_task/' + taskId + '/' + name;
    } else {
        alert('La tarea está en progreso. Por favor, espera...');
    }
}
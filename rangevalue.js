var sliders = document.querySelectorAll("#slider");
for (var i = 0; i < sliders.length; i++) {
  sliders[i].onchange = function(e) {
      e.target.previousElementSibling.innerHTML = e.target.value
   }
}

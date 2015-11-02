function toggle(source, name) {
  checkboxes = document.getElementsByClassName(name);
  for(var i=0, n=checkboxes.length;i<n;i++) {
    checkboxes[i].checked = source.checked;
  }
}

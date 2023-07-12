
//lettering.js
//function to add text letter by letter
function lettering(target, message, index, interval, action) {
  if(/^([ ,.;:\[\]\{\}\(\)-_=+|\\\/])$/.test(message[index]) || message.length == index){
    $(target).lettering("words"); 
  }
  if (index < message.length) {
    $(target).html($(target).html()+message[index++]);
    setTimeout(function() {
      lettering(target, message, index, interval, action);
    }, interval);
  }
  else{
    action()
  }
}
$(document).ready(function () {
  $('#nav-tabs').on('click', function () {
    $('#nav-item').toggleClass('active');
  });
});

function setCompany(name){
  var titleInput = name;
  if (titleInput) {
      // Create Ajax Call
      $.ajax({
          url: '/setSessionCompany',
          type: 'GET',
          data: {
              'title': titleInput,
          },
          dataType: 'json',
          success: function (data) {
            if (data.instance) {
                location.reload();
                e.preventDefault();
            }else{

            }
          },
          error: function(xhr, status, error) {
            alert('error = ' + error);
          }
      });
  } else {
  
  }
  return false;
}


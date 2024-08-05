function verCarrito(urls){
    $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#optenerProducto").html(resp);
        }
    });
  }
function mostrar_buscador(){
  $('.menus').slideToggle(1000);
  $('.menus form #shear_text').focus();
}

function newProducto(urls){
  $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#team_productos .productos_por_categorias").html(resp);
        }
    });
}
function updateUser(urls){
  $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#team_productos .productos_por_categorias").html(resp);
        }
    });
}
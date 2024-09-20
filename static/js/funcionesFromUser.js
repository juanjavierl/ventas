function verCarrito(urls){
    $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#optenerProducto").html(resp);
        }
    });
  }
function mostrar_buscador(id_company){
  $('.menus').slideToggle(1000);
  $('.menus form #shear_text').focus();
}

function newProducto(urls){
    
  $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("section .productos_por_categorias").html(resp);
            $(".navbar-mobile i").click();
            
        }
    });
}
function updateUser(urls){
  $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#team_productos .productos_por_categorias").html(resp);
            $(".navbar-mobile i").click();
        }
    });
}

function add_hivicacion(urls){
    $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $(".modal-content").html(resp);
            $(".navbar-mobile i").click();
        }
    });
}
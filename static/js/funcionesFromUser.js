function verCarrito(urls){
    $.ajax({
        type:'GET',
        url:urls,
        success:function(resp){
            $("#optenerProducto").html(resp);
        }
    });
  }

function updateProductosEnConfirmar(urls){
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (respuesta) {
            $('#carritos_items').html(respuesta);
        }
    })
}

function updateTotalPago(urls, valor_option){
    $.ajax({
        type:'GET',
        url:urls,
        data:{'opcion':valor_option},
        success:function(resp){
          $('#costos').text("Importe: "+ resp.datos.importe + " Precio de envio: "+ resp.datos.precio_envio + " Total a pagar : Bs." + resp.datos.total_pagar)
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
            $("#team_productos .productos_por_categorias").html(resp);
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
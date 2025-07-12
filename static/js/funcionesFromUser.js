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
let buscadorCargado = false;
function mostrar_buscador(id_company) {
    const contenedor = $(".form_buscador_product");
    if (!buscadorCargado) {
        $.ajax({
            type: 'GET',
            url: '/form_sheart_product/',
            data: { 'id_company': id_company },
            success: function (resp) {
                contenedor.html(resp);
                contenedor.slideDown(300, function () {
                    $('#shear_text').focus(); // Foco al input una vez que se muestra
                });
                buscadorCargado = true;
                // Scroll a productos después de mostrar el buscador
                $('html, body').animate({
                    scrollTop: $(".productos_por_categorias").offset().top - 80
                }, 600);
            },
            error: function () {
                contenedor.html('<div class="alert alert-danger">Error al cargar buscador</div>');
            }
        });
    } else {
        contenedor.slideToggle(300, function () {
            if (contenedor.is(':visible')) {
                $('#shear_text').focus();
            }
        });

        // Siempre hacer scroll al contenedor de productos
        $('html, body').animate({
            scrollTop: $(".productos_por_categorias").offset().top - 80
        }, 600);
    }
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
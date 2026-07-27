//REPORTES POR FECHA Y ID ORDEN
$(function () {
    $('.pedidos').hide();//escondo solo para que muestre con decenio
    var date_now = new moment().format('DD-MM-YYYY');//optengo la fecha actual
    $('#form_by_date input[name="daterange"]').daterangepicker({
        //opens: 'left'
        locale: {
            format: 'DD/MM/YYYY',
            applyLabel: 'Aplicar',
            canvelLabel: 'Cancelar'
        },
        minYear: 2024,
        "startDate": date_now,
        "endDate": date_now
    }, function (start, end, label) {

        reportBydate(start.format('DD-MM-YYYY'), end.format('DD-MM-YYYY'))
    });
});

function reportBydate(startDate, endDate) {
    let datos = {
        'startDate': startDate,
        'endDate': endDate,
        'id_company': APP.companyId,
        csrfmiddlewaretoken: APP.csrfToken
    }
    $.ajax({
        type: 'POST',
        url: $('#form_by_date').attr('action'),
        data: datos,
        success: function (resp) {
            if (resp) {
                $('.pedidos').fadeIn('slow').html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(thrownError);
            mostrar_notificacion();
        }
    });
    return false;
}

$('#form_buscar_orden').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (resp) {
            if (resp) {
                $('.pedidos').fadeIn('slow').html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(thrownError);
            mostrar_notificacion();
        }
    });
});

function form_company(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },// Marca como AJAX
        success: function (resp) {
            $(".modal-content").html(resp);
            $(".navbar-mobile i").click();
        }
    });
}

// PRECIOS DE ENVIO
$('#form_precio_envio').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (resp) {
            let mensaje = '';
            if (resp.errors) {
                for (const campo in resp.errors) {
                    resp.errors[campo].forEach(function (error) {
                        mensaje += error.message + '<br>';
                    });
                }
                $('.toast-body').addClass('alert alert-danger');
                $('.toast-body').fadeIn(1000).html(mensaje);
                mostrar_notificacion();
            } else {
                $(".precios_env").html("");
                $('.toast-body').addClass('alert alert-success');
                $('.toast-body').fadeIn(1000).html(resp.success);
                mostrar_notificacion();
                $.ajax({
                    type: 'GET',
                    url: '/' + APP.companyId + '/mostrar_precio',
                    success: function (respuesta) {
                        $('#delete_precio').html(respuesta);
                    }

                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html("verifique si tiene internet");
            mostrar_notificacion();
        }
    });
});

function del_precio(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            if (resp.error) {
                $(".invalid_ct").html(resp.error);
            } else {

                $(".modal-content").html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert("Error:" + thrownError);
        }
    });
    return false;
}

// REGISTRO DE BANCO
$('#form_banco_envio').on('submit', function (e) {
    e.preventDefault();
    let datos = new FormData(this);
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: datos,
        contentType: false,
        processData: false,
        success: function (resp) {
            if (resp.success) {
                $('.toast-body').addClass('alert alert-success');
                $('.toast-body').fadeIn(1000).html(resp.success);
                mostrar_notificacion();
                $.ajax({
                    type: 'get',
                    url: '/' + APP.companyId + '/infor_banco',
                    success: function (resp) {
                        $('.info_banco').html(resp);
                    }

                });
            } else {
                $('.toast-body').addClass('alert alert-danger');
                $('.toast-body').fadeIn(1000).html(resp.error);
                mostrar_notificacion();
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(resp.error);
            mostrar_notificacion(resp.error);
        }
    });
});

function del_infor_comp(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            if (resp.error) {
                $(".invalid_ct").html(resp.error);
            } else {

                $(".modal-content").html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(thrownError);
            mostrar_notificacion();
        }
    });
    return false;
}

//REGISTRO DE AVISOS
$('#add_avisos_forms').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (resp) {
            if (resp) {
                $('.toast-body').addClass('alert alert-success');
                $('.toast-body').fadeIn(1000).html(resp.success);
                mostrar_notificacion();
                $.ajax({
                    type: 'get',
                    url: '/' + APP.companyId + '/get_opciones',
                    success: function (resp) {
                        $('.info_avisos').html(resp);
                    }

                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html("Error: " + thrownError);
            mostrar_notificacion();
        }
    });
});
function elimnarOpciones(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            if (resp.error) {
                $(".invalid_ct").html(resp.error);
            } else {

                $(".modal-content").html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(thrownError);
            mostrar_notificacion();
        }
    });
    return false;
}

// inventario productos
function imprimirLista(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            $(".modal-content").html(resp);
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert("Error:" + thrownError);
        }
    });
}
$("#filterProduct #invProduct").change(function(){
        $.ajax({
            type: 'POST',
            url: $('#filterProduct').attr('action'),
            data: $("#filterProduct").serialize(),
            success: function (resp) {
                if (resp) {
                    $('.inventarioProductos').fadeIn('slow').html(resp);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                $('.toast-body').addClass('alert alert-danger');
                $('.toast-body').fadeIn(1000).html(thrownError);
                mostrar_notificacion();
            }
        });
        return false;
    });
// REGISTRO DE UBICACION
class Localizacion {
    constructor(callback) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                this.latitude = position.coords.latitude;
                this.longitude = position.coords.longitude;
                callback();
            });
        } else {
            alert("Tu navegador no soporta geolocalizacion")
        }
    }
}

function initMap() {
    const ubicacion = new Localizacion(() => {
        const mylatLng = { lat: ubicacion.latitude, lng: ubicacion.longitude }

        $("#id_latitud").val(ubicacion.latitude);
        $("#id_longitud").val(ubicacion.longitude);
        const options = {
            center: mylatLng,
            zoom: 15
        }
        var map = document.getElementById('map');
        const mapa = new google.maps.Map(map, options);

        const marker = new google.maps.Marker({
            //const marker = new google.maps.marker.AdvancedMarkerElement({
            map: mapa,
            position: mylatLng,
            title: 'Mi ubicación',
            draggable: true,
        });
        google.maps.event.addListener(marker, 'position_changed', function () {
            getMarkerCoords(marker);
        });
        function getMarkerCoords(marker) {
            var markerCoords = marker.getPosition();
            $('#id_latitud').val(markerCoords.lat);
            $('#id_longitud').val(markerCoords.lng);
        }

    });
}

/* $('#add_hivicacion_forms').on('submit', function (e) {
e.preventDefault();
$.ajax({
    type: 'POST',
    url: $(this).attr('action'),
    data: $(this).serialize(),
    success: function (resp) {
        if (resp.error) {
            $(".invalid_ct").html(resp.error);
        } else {

            $(".btn-close").click();
        }
    },
    error: function (xhr, ajaxOptions, thrownError) {
        alert("Error:" + thrownError);
    }
});
}); */
$('#form_add_mapa').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (resp) {
            if (resp.success) {
                $('.toast-body').addClass('alert alert-success');
                $('.toast-body').fadeIn(1000).html(resp.success);
                mostrar_notificacion();
                $.ajax({
                    type: 'GET',
                    url: '/' + APP.companyId + '/info_address_company',
                    success: function (resp) {
                        $('.info_map_registro').fadeIn(1000).html(resp.address);
                    }
                });

            } else {
                $('.toast-body').addClass('alert alert-danger');
                $('.toast-body').fadeIn(1000).html('Ya existe un registro');
                mostrar_notificacion();
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html('Error: ' + thrownError);
            mostrar_notificacion('Error: ' + thrownError);
        }
    });
});

function del_address_comp(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            if (resp.error) {
                $(".invalid_ct").html(resp.error);
            } else {

                $(".modal-content").html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html(thrownError);
            mostrar_notificacion();
        }
    });
    return false;
}

// REGISTROS DE TERMINOS Y CONDICIONES
$('#add_regla_forms').on('submit', function (e) {
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (resp) {
            if (resp.error) {
                $('.toast-body').addClass('alert alert-danger');
                $('.toast-body').fadeIn(1000).html(resp.error);
                mostrar_notificacion();
            } else {
                $(".precios_env").html("");
                $('.toast-body').addClass('alert alert-success');
                $('.toast-body').fadeIn(1000).html(resp.success);
                mostrar_notificacion();
                $.ajax({
                    type: 'GET',
                    url: '/' + APP.companyId + '/get_condiciones',
                    success: function (resp) {
                        $('.info_rule').html(resp);
                    }

                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            $('.toast-body').addClass('alert alert-danger');
            $('.toast-body').fadeIn(1000).html("Ya existe las condiciones");
            mostrar_notificacion();
        }
    });
});

function del_regla(urls) {
    $.ajax({
        type: 'GET',
        url: urls,
        success: function (resp) {
            if (resp.error) {
                $(".invalid_ct").html(resp.error);
            } else {

                $(".modal-content").html(resp);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            alert("Error:" + thrownError);
        }
    });
    return false;
}


$(document).ready(function () {
    // Quita el alert que impide la carga normal de la página
    // alert("Script for add_ofertas.html is running.");

    // Asegura que los elementos existen antes de usarlos
    const slider = $('#id_descuento');
    const valor = $('#id_descuento_helptext');

    if (slider.length && valor.length) {
        // Mostrar el valor inicial
        valor.text('Descuento: ' + slider.val() + '%');
        // Actualizar mientras se mueve
        slider.on('input', function () {
            valor.text('Descuento: ' + $(this).val() + '%');
        });
    }

    // Activa los calendarios solo si los elementos existen

    console.log("Fecha inicio:", $('#id_fecha_inicio').val());
    console.log("Fecha fin:", $('#id_fecha_fin').val());

    if ($('#id_fecha_inicio').length) {
        $('#id_fecha_inicio').daterangepicker({
            singleDatePicker: true,
            autoApply: true,
            autoUpdateInput: true,
            minDate: moment(),
            locale: {
                format: 'DD/MM/YYYY',
                applyLabel: 'Aceptar',
                cancelLabel: 'Cancelar',
                daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
                monthNames: [
                    'Enero', 'Febrero', 'Marzo', 'Abril',
                    'Mayo', 'Junio', 'Julio', 'Agosto',
                    'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                ],
                firstDay: 1
            }
        });
    }
    if ($('#id_fecha_fin').length) {
        $('#id_fecha_fin').daterangepicker({
            singleDatePicker: true,
            autoApply: true,
            minDate: moment(),
            locale: {
                format: 'DD/MM/YYYY',
                applyLabel: 'Aceptar',
                cancelLabel: 'Cancelar',
                daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
                monthNames: [
                    'Enero', 'Febrero', 'Marzo', 'Abril',
                    'Mayo', 'Junio', 'Julio', 'Agosto',
                    'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                ],
                firstDay: 1
            }
        });
    }
    $('#add_ofertas_forms').on('submit', function (e) {
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function (resp) {
                if (resp.success) {
                    $('.toast-body').removeClass('alert-danger').addClass('alert-success').fadeIn(1000).html('<strong>' + resp.success + '</strong>');

                    mostrar_notificacion();
                    $.ajax({
                        type: 'GET',
                        url: '/get_promocion/' + APP.companyId,
                        success: function (data) {
                            console.log(data);
                            $('.info_ofertas').html(data);
                        },
                        error: function (xhr, ajaxOptions, thrownError) {
                            alert("Error: " + thrownError);
                        }
                    });
                } else {
                    $('.toast-body').removeClass('alert-success').addClass('alert-danger').fadeIn(1000).html('<strong>' + resp.error + '</strong>');
                    mostrar_notificacion();
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert("Error: " + thrownError);
            }
        });
    });
});
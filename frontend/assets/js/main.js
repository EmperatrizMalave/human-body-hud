(function($) {
    "use strict";
  
    const $documentOn = $(document);
    const $windowOn = $(window);
  
    $documentOn.ready( function() {
  
      /* ================================
       Mobile Menu Js Start
    ================================ */
    
    $('#mobile-menu').meanmenu({
        meanMenuContainer: '.mobile-menu',
        meanScreenWidth: "1199",
        meanExpand: ['<i class="far fa-plus"></i>'],
    });
    
     /* ================================
       Sidebar Toggle Js Start
    ================================ */

      $(".offcanvas__close,.offcanvas__overlay").on("click", function () {
        $(".offcanvas__info").removeClass("info-open");
        $(".offcanvas__overlay").removeClass("overlay-open");
      });
      $(".sidebar__toggle").on("click", function () {
        $(".offcanvas__info").addClass("info-open");
        $(".offcanvas__overlay").addClass("overlay-open");
      });
      
       /* ================================
       Body Overlay Js Start
    ================================ */

      $(".body-overlay").on("click", function () {
        $(".offcanvas__area").removeClass("offcanvas-opened");
        $(".df-search-area").removeClass("opened");
        $(".body-overlay").removeClass("opened");
      });
  
      /* ================================
       Sticky Header Js Start
    ================================ */

      $windowOn.on("scroll", function () {
        if ($(this).scrollTop() > 250) {
          $("#header-sticky").addClass("sticky");
        } else {
          $("#header-sticky").removeClass("sticky");
        }
      });      
      
       /* ================================
       Video & Image Popup Js Start
    ================================ */

      $(".img-popup").magnificPopup({
        type: "image",
        gallery: {
          enabled: true,
        },
      });

      $(".video-popup").magnificPopup({
        type: "iframe",
        callbacks: {},
      });
  
      /* ================================
       Counterup Js Start
    ================================ */

      $(".gt-count").counterUp({
        delay: 15,
        time: 4000,
      });
  
      /* ================================
       Wow Animation Js Start
    ================================ */

      new WOW().init();
  
      /* ================================
       Nice Select Js Start
    ================================ */

    if ($('.single-select').length) {
        $('.single-select').niceSelect();
    }

     /* ================================
      Team ACTIVE Js Start
    ================================ */
    const getSlide = $('gt-team-wrapper, .team-box-img-2').length - 1;
    const slideCal = 100 / getSlide + '%';
    
    $('.project-wrapper').css({
        "width": slideCal
    });
    
    $(document).on('mouseenter', '.team-box-img-2', function() {
        $('.team-box-img-2').removeClass('active');
        $(this).addClass('active');
    });     


     /* ================================
       GT Brand Slider Js Start
    ================================ */

    if($('.gt-brand-slider').length > 0) {
        const gtBrandSlider = new Swiper(".gt-brand-slider", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".array-prev",
                prevEl: ".array-next",
            },
            breakpoints: {
                1199: {
                    slidesPerView: 5,
                },
                991: {
                    slidesPerView: 4,
                },
                767: {
                    slidesPerView: 3,
                },
                575: {
                    slidesPerView: 2,
                },
                400: {
                    slidesPerView: 2,
                },
            },
        });
    }

     /* ================================
       GT training Slider Js Start
    ================================ */

    if($('.gt-training-slider').length > 0) {
        const gtTrainingSlider = new Swiper(".gt-training-slider", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".array-prev",
                prevEl: ".array-next",
            },
            breakpoints: {
                1199: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 2,
                },
                767: {
                    slidesPerView: 2,
                },
                575: {
                    slidesPerView: 1,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });
    }
    
     /* ================================
       GT Team Slider Js Start
    ================================ */
    if($('.gt-team-slider').length > 0) {
        const gtTeamSlider = new Swiper(".gt-team-slider", {
          effect: "coverflow",
          spaceBetween: 60,
          autoplay: true,
          centeredSlides: true,
          loop: true,
          autoplay: {
            delay: 2000,
            disableOnInteraction: false,
          },
          coverflowEffect: {
              rotate: 50,
              stretch: 0,
              depth: 100,
              modifier: 1,
              slideShadows: false,
              scale: 1
          },

          navigation: {
                nextEl: ".array-prev",
                prevEl: ".array-next",
            },

          breakpoints: {
                1399: {
                    slidesPerView: 3,
                     spaceBetween: 60,
                },
                 1199: {
                    slidesPerView: 3,
                    spaceBetween: 30,
                },
                991: {
                    slidesPerView: 2,
                    spaceBetween: 30,
                },
                767: {
                    slidesPerView: 2,
                    spaceBetween: 30,
                },
                575: {
                    slidesPerView: 1,
                    spaceBetween: 30,
                },
                0: {
                    slidesPerView: 1,
                },
          },
        });
    }

     /* ================================
      GT Marque Slider Js Start
    ================================ */
    if($('.marque-text-slider').length > 0) {
      const marqueTextSlider = new Swiper(".marque-text-slider", {
          slidesPerView: 'auto',
          spaceBetween: 48,
          freemode: true,
          centeredSlides: true,
          loop: true,
          speed: 9000,
          allowTouchMove: false,
          autoplay: {
              delay: 1,
              disableOnInteraction: true,
          },
      });
    }

    /* ================================
       GT Testimonial Slider Js Start
    ================================ */

    if($('.gt-testimonial-slider2').length > 0) {
        const gtTestimonialSlider2 = new Swiper(".gt-testimonial-slider2", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".array-prev",
                prevEl: ".array-next",
            },
            breakpoints: {
                1199: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 2,
                },
                767: {
                    slidesPerView: 2,
                },
                575: {
                    slidesPerView: 1,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });
    }

   
    if ($('.gt-testimonial-slider').length > 0 && $('.swiper-image').length > 0) {

        const imageSwiper = new Swiper('.swiper-image', {
        effect: 'cards',
        grabCursor: true,
        loop: true,
        keyboard: {
        enabled: true,
        onlyInViewport: false,
        },
        navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
        },
        cardsEffect: {
        rotate: 0,
        perSlideRotate: 0,
        perSlideOffset: 3
        },
        });
        
        const contentSwiper = new Swiper('.gt-testimonial-slider', {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        autoplay: {
        delay: 2000,
        disableOnInteraction: false,
        },
        navigation: {
        nextEl: '.array-prev',
        prevEl: '.array-next',
        },
        breakpoints: {
        0: { slidesPerView: 1 },
        575: { slidesPerView: 1 },
        767: { slidesPerView: 1 },
        991: { slidesPerView: 1 },
        1199: { slidesPerView: 1 },
        1399: { slidesPerView: 1 },
        },
        });
        
        // Link the two Swipers
        contentSwiper.controller.control = imageSwiper;
        imageSwiper.controller.control = contentSwiper;
    }

    if($('.gt-content-slider').length > 0) {
        const gtContentSlider = new Swiper(".gt-content-slider", {
        spaceBetween: 30,
        speed: 1300,
        loop: true,
        centeredSlides: true,
        autoplay: {
            delay: 2000,
            disableOnInteraction: false,
        },
        breakpoints: {
            1399: {
                slidesPerView: 1,
            },
            1199: {
                slidesPerView: 1,
            },
            991: {
                slidesPerView: 1,
            },
            767: {
                slidesPerView: 1,
            },
            575: {
                slidesPerView: 1,
            },
            0: {
                slidesPerView: 1,
            },
        },
    });
  }

     /* ================================
       GT Training Slider Js Start
    ================================ */

    if($('.gt-training-slider-2').length > 0) {
         const gtTrainingSlider2 = new Swiper(".gt-training-slider-2", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            breakpoints: {
                1399: {
                    slidesPerView: 4,
                },
                1199: {
                    slidesPerView: 3,
                },
                991: {
                    slidesPerView: 2,
                },
                767: {
                    slidesPerView: 2,
                },
                575: {
                    slidesPerView: 1,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });
    }

   /* ================================
       GT Instagram Slider Js Start
    ================================ */

     if($('.gt-instagram-banner-slider').length > 0) {
        const gtIinstagramBannerSlider = new Swiper(".gt-instagram-banner-slider", {
            spaceBetween: 30,
            speed: 1300,
            loop: true,
            centeredSlides: true,
            autoplay: {
                delay: 2000,
                disableOnInteraction: false,
            },
            navigation: {
                nextEl: ".array-prev",
                prevEl: ".array-next",
            },
            breakpoints: {
                1399: {
                    slidesPerView: 7,
                },
                1199: {
                    slidesPerView: 6,
                },
                991: {
                    slidesPerView: 4,
                },
                767: {
                    slidesPerView: 3,
                },
                575: {
                    slidesPerView: 2,
                },
                0: {
                    slidesPerView: 1,
                },
            },
        });
    }

   /* ================================
       Parallaxie Js Start
    ================================ */

        if ($('.parallaxie').length && $(window).width() > 991) {
            if ($(window).width() > 768) {
                $('.parallaxie').parallaxie({
                    speed: 0.55,
                    offset: 0,
                });
            }
        }
        

     /* ================================
       Mouse Cursor Animation Js Start
    ================================ */

    if ($(".mouseCursor").length > 0) {
        function itCursor() {
            var myCursor = jQuery(".mouseCursor");
            if (myCursor.length) {
                if ($("body")) {
                    const e = document.querySelector(".cursor-inner"),
                        t = document.querySelector(".cursor-outer");
                    let n,
                        i = 0,
                        o = !1;
                    (window.onmousemove = function(s) {
                        o ||
                            (t.style.transform =
                                "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                            (e.style.transform =
                                "translate(" + s.clientX + "px, " + s.clientY + "px)"),
                            (n = s.clientY),
                            (i = s.clientX);
                    }),
                    $("body").on(
                            "mouseenter",
                            "button, a, .cursor-pointer",
                            function() {
                                e.classList.add("cursor-hover"),
                                    t.classList.add("cursor-hover");
                            }
                        ),
                        $("body").on(
                            "mouseleave",
                            "button, a, .cursor-pointer",
                            function() {
                                ($(this).is("a", "button") &&
                                    $(this).closest(".cursor-pointer").length) ||
                                (e.classList.remove("cursor-hover"),
                                    t.classList.remove("cursor-hover"));
                            }
                        ),
                        (e.style.visibility = "visible"),
                        (t.style.visibility = "visible");
                }
            }
        }
        itCursor();
      }
  
      /* ================================
       Search Popup Toggle Js Start
    ================================ */

    if ($(".search-toggler").length) {
        $(".search-toggler").on("click", function(e) {
            e.preventDefault();
            $(".search-popup").toggleClass("active");
            $("body").toggleClass("locked");
        });
    }

    /* ================================
        Quantity Increment/Decrement Js Start
    ================================ */
    const quantityButtons = document.querySelectorAll(".quantityIncrement, .quantityDecrement");
    if (quantityButtons.length) {
        quantityButtons.forEach((button) => {
            button.addEventListener("click", function () {
                const input = button.parentElement.querySelector("input");
                let value = parseInt(input.value, 10) || 0;

                if (button.classList.contains("quantityIncrement")) {
                    input.value = value + 1;
                } else if (button.classList.contains("quantityDecrement") && value > 1) {
                    input.value = value - 1;
                }
            });
        });
    }

    /* ================================
       Payment Method Update Js Start
    ================================ */

    function updatePaymentMethod() {
        let paymentMethod = $("input[name='pay-method']:checked").val();
        $(".payment").html(paymentMethod);
    }

    // Initial load
    updatePaymentMethod();

    // On click of radio option
    $(".checkout-radio-single input[name='pay-method']").on("change", function () {
        updatePaymentMethod();
    });
    
    /* ================================
       Additional Quantity Controls Js Start
    ================================ */

    const inputs = document.querySelectorAll('#qty, #qty2, #qty3');
    const btnminus = document.querySelectorAll('.qtyminus');
    const btnplus = document.querySelectorAll('.qtyplus');

    if (inputs.length > 0 && btnminus.length > 0 && btnplus.length > 0) {

        inputs.forEach(function(input, index) {
            const min = Number(input.getAttribute('min'));
            const max = Number(input.getAttribute('max'));
            const step = Number(input.getAttribute('step'));

            function qtyminus(e) {
                const current = Number(input.value);
                const newval = (current - step);
                if (newval < min) {
                    newval = min;
                } else if (newval > max) {
                    newval = max;
                }
                input.value = Number(newval);
                e.preventDefault();
            }

            function qtyplus(e) {
                const current = Number(input.value);
                const newval = (current + step);
                if (newval > max) newval = max;
                input.value = Number(newval);
                e.preventDefault();
            }

            btnminus[index].addEventListener('click', qtyminus);
            btnplus[index].addEventListener('click', qtyplus);
        });
    }
  

   /* ================================
       Back To Top Button Js Start
    ================================ */

    $windowOn.on('scroll', function() {
        if ($(this).scrollTop() > 20) {
            $("#gt-back-top").addClass("show");
        } else {
            $("#gt-back-top").removeClass("show");
        }
    });
    
    $documentOn.on('click', '#gt-back-top', function() {
        $('html, body').animate({ scrollTop: 0 }, 800);
        return false;
    });



    
    }); // End Document Ready Function


    function loader() {
        $(window).on('load', function() {
            // Animate loader off screen
            $(".preloader").addClass('loaded');                    
            $(".preloader").delay(600).fadeOut();                       
        });
    }

    loader();

  
  })(jQuery); // End jQuery
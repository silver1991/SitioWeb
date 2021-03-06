from django.shortcuts import render
from django.views.generic.edit import UpdateView
from Foro.forms import *
from PIL import Image as PImage
from django.shortcuts import redirect
from django.core.urlresolvers import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from Foro.util import redir
from SitioWeb.settings import MEDIA_URL
from django.contrib.auth import authenticate


# Create your views here.

class HomeForo(ListView):
    queryset = Foro.objects.filter(estado=1)
    template_name = "foro/listaForos.html"
    paginate_by = 15


class ListaTemas(ListView):
    model = Tema
    template_name = "foro/listaTemas.html"
    paginate_by = 15

    def get_queryset(self, **kwargs):
        return Tema.objects.filter(foro=self.kwargs.get('pk'), estado=1)

    def get_context_data(self, **kwargs):
        context = super(ListaTemas, self).get_context_data()
        context['foro'] = Foro.objects.filter(id=self.kwargs.get('pk'), estado=1)[0]
        return context


class ListaMensajes(ListView):
    Model = Mensaje
    template_name = "foro/listaMensajes.html"
    paginate_by = 15

    def get_queryset(self, **kwargs):
        return Mensaje.objects.filter(tema=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super(ListaMensajes, self).get_context_data()
        context['tema'] = Tema.objects.filter(id=self.kwargs.get('pk'))[0]
        context['media_url'] = MEDIA_URL
        return context


class DetalleUsuario(DetailView):
    model = PerfilUsuario
    template_name = "foro/detalleUsuario.html"


class ListaTemasUsuario(ListView):
    model = Tema
    template_name = "foro/temasPorUsuario.html"
    paginate_by = 15

    def get_queryset(self, **kwargs):
        return Tema.objects.filter(autor=self.kwargs.get('pk'), estado=1)

    def get_context_data(self, **kwargs):
        context = super(ListaTemasUsuario, self).get_context_data()
        context['usuario'] = User.objects.filter(id=self.kwargs.get('pk'))[0]
        return context


class ListaMensajesUsuario(ListView):
    model = Mensaje
    template_name = "foro/mensajesPorUsuario.html"
    paginate_by = 15

    def get_queryset(self, **kwargs):
        return Mensaje.objects.filter(autor=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super(ListaMensajesUsuario, self).get_context_data()
        context['usuario'] = User.objects.filter(id=self.kwargs.get('pk'))[0]
        context['media_url'] = MEDIA_URL
        return context


def MensajeCensura(request, **kwargs):
    pk = kwargs.get("pk")
    mensaje=Mensaje.objects.filter(id=pk)[0]
    form=FormMensaje
    context={'mensaje':mensaje,'form':form,'media_url':MEDIA_URL}
    return render(request,'foro/msjCensura.html',context)

def ConfirmarCensura(request):
    p = request.POST
    mensaje=Mensaje.objects.filter(id=p["id"])[0]
    mensaje.apropiado=p.get('apropiado', False)
    mensaje.save()
    return redirect('mensajes', pk=mensaje.tema.id)


def EditarMensaje(request, **kwargs):
    pk = kwargs.get("pk")
    mensaje=Mensaje.objects.filter(id=pk)[0]
    form=EditorWYSIWYG(initial={'mensaje':mensaje.contenido})
    context={'mensaje':mensaje,'form':form,'media_url':MEDIA_URL}
    return render(request,'foro/editarMensaje.html',context)


def ConfirmarEdicion(request):
    p = request.POST
    mensaje=Mensaje.objects.filter(id=p["id"])[0]
    mensaje.editado=True
    mensaje.contenido=p.get('mensaje')
    mensaje.save()
    return redirect('mensajes', pk=mensaje.tema.id)

def CitarMensaje(request, **kwargs):
    pk = kwargs.get("pk")
    mensaje=Mensaje.objects.filter(id=pk)[0]
    cita="[q]<b>"+mensaje.autor.username+"</b> : <br>"+mensaje.contenido+"[/q]"
    form=EditorWYSIWYG(initial={'mensaje':cita})
    context={'form':form,'mensaje':mensaje}
    return render(request,'foro/citarMensaje.html',context)

class EditarPerfil(UpdateView):
    model = PerfilUsuario
    form_class = FormPerfil
    success_url = "#"
    template_name = "foro/perfil.html"

    def form_valid(self, form):
        """Resize and save profile image."""
        # remove old image if changed
        name = form.cleaned_data.get("avatar")
        pk = self.kwargs.get("pk")
        old = PerfilUsuario.objects.get(pk=pk).avatar

        if old.name and old.name != name:
            old.delete()

        # save new image to disk & resize new image
        self.form_object = form.save()

        if self.form_object.avatar:
            img = PImage.open(self.form_object.avatar.path)
            img.thumbnail((160, 160), PImage.ANTIALIAS)
            img.save(img.filename, "JPEG")

        return redir(self.success_url)


class EditarUsuario(UpdateView):
    model = User
    form_class = EditUserForm
    template_name = "foro/editarUsuario.html"

    def get_success_url(self):
        return reverse_lazy('editar_perfil', args=(self.object.id,))


def NuevoTema(request, **kwargs):
    pk = kwargs.get("pk")
    foro = Foro.objects.filter(id=pk)[0]
    form=EditorWYSIWYG
    context = {"foro": foro,'form':form}
    return render(request, "foro/nuevoTema2.html", context)


def CrearTema(request):
    p = request.POST
    if p["tema"] and p["mensaje"]:
        foro = Foro.objects.filter(id=p["foro"])[0]
        tema = Tema.objects.create(titulo=p["tema"], foro=foro, autor=request.user)
        Mensaje.objects.create(tema=tema, autor=request.user, contenido=p["mensaje"])
        request.user.perfil.incrementar_mensaje()
        return redirect('mensajes', pk=tema.id)
    else:
        return redirect('home')


def NuevoMensaje(request, **kwargs):
    pk = kwargs.get("pk")
    tema = Tema.objects.filter(id=pk, estado=1)[0]
    form=EditorWYSIWYG
    context = {"tema": tema,'form':form}
    return render(request, "foro/nuevoMensaje2.html", context)


def CrearMensaje(request):
    p = request.POST
    if p["mensaje"]:
        tema = Tema.objects.filter(id=p["tema"], estado=1)[0]
        Mensaje.objects.create(tema=tema, autor=request.user, contenido=p["mensaje"])
        request.user.perfil.incrementar_mensaje()
        return redirect('mensajes', pk=tema.id)
    else:
        return redirect('home')

class BuscarContenido(ListView):
    Model = Mensaje
    template_name = "foro/resultadoBusqueda.html"
    paginate_by = 15

    def get_queryset(self, **kwargs):
        print(self.request.GET.get('texto'))
        return Mensaje.objects.filter(contenido__search=self.request.GET.get('texto'))

    def get_context_data(self, **kwargs):
        context = super(BuscarContenido, self).get_context_data()
        context['texto'] = self.request.GET.get('texto')
        context['media_url'] = MEDIA_URL
        return context




def DesactivarCuenta(request):
    password=request.POST.get('password')
    usuario=request.user
    if usuario.check_password(password):
       usuario.is_active=False
       usuario.save()
       return redirect('/accounts/logout/?next=/')
    else:
       context={'mensaje':'Contraseña incorrecta'}
       return render(request,'foro/desactivarCuenta.html',context)


def ActivarCuenta(request):
    password=request.POST.get('password')
    username=request.POST.get('username')
    usuario=authenticate(username=username,password=password)
    if usuario:
       if usuario.is_active:
          context={'mensaje':'Esta cuenta está activada'}
          return render(request,'foro/activarCuenta.html',context)
       else:
         usuario.is_active=True
         usuario.save()
         return redirect('registration_activation_complete')
    else:
       context={'mensaje':'No existe el usuario'}
       return render(request,'foro/activarCuenta.html',context)

def prueba(request):
    form=AnotherForm
    context={'form':form}
    return render(request,'prueba.html',context)


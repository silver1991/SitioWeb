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


# Create your views here.

class HomeForo(ListView):
    queryset =Foro.objects.filter(estado=1)
    template_name = "foro/listaForos.html"
    paginate_by = 15



class ListaTemas(ListView):
    model = Tema
    template_name = "foro/listaTemas.html"
    paginate_by = 15


    def get_queryset(self,**kwargs):
        return Tema.objects.filter(foro=self.kwargs.get('pk'), estado=1)

    def get_context_data(self, **kwargs):
        context = super(ListaTemas, self).get_context_data()
        context['foro'] = Foro.objects.filter(id=self.kwargs.get('pk'),estado=1)[0]
        return context


class ListaMensajes(ListView):
    Model=Mensaje
    template_name = "foro/listaMensajes.html"
    paginate_by = 15


    def get_queryset(self,**kwargs):
        return Mensaje.objects.filter(tema=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        context = super(ListaMensajes, self).get_context_data()
        context['tema'] = Tema.objects.filter(id=self.kwargs.get('pk'))[0]
        context['media_url'] = MEDIA_URL
        return context


class DetalleUsuario(DetailView):
    model = PerfilUsuario


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


def NuevoTema(request,**kwargs):
    pk=kwargs.get("pk")
    foro=Foro.objects.filter(id=pk)[0]
    context={"foro":foro}
    return render(request,"foro/nuevoTema.html",context)


def CrearTema(request):
    p=request.POST
    if p["tema"] and p["mensaje"]:
        foro=Foro.objects.filter(id=p["foro"])[0]
        tema=Tema.objects.create(titulo=p["tema"], foro=foro,autor=request.user)
        Mensaje.objects.create(tema=tema,autor=request.user,contenido=p["mensaje"])
        request.user.perfil.incrementar_mensaje()
        return redirect('mensajes', pk=tema.id)
    else:
        return redirect('home')


{% set active_page='login' %}{% extends "layout2.html" %}
{% block title %}{{ _('Login') }}{% endblock %}
{% block content %}
    <h1>{{ _('Login') }}</h1>
    <p class="lead">{{ _('Please log in to access this area.') }}</p>
    <form method="POST" class="form-horizontal">
      <b-form-group
        label="{{ _('Username') }}"
        label-cols-sm="2"
        for="username">
        <b-form-input name="username" id="username"></b-form-input>
      </b-form-group>
      <b-form-group
        label="{{ _('Password') }}"
        label-cols-sm="2"
        for="password">
        <b-form-input type="password" name="password" id="password"></b-form-input>
      </b-form-group>

      <div class="form-group form-check">
        <div class="col-sm-12">
          <div class="checkbox">
            <label for="remember">
              <input type="checkbox" id="remember" name="remember"> Remember me
            </label>
          </div>
        </div>
      </div>
      <b-form-group>
        <button type="submit" class="btn btn-default btn-primary"
          id="submit">{{ _('Log in') }}</button>
      </b-form-group>
      <b-form-group>
        <a href="{{ url_for('users.reset_password') }}">Forgot your password? Reset it here</a>.
      </b-form-group>
    </form>

{% endblock %}
{% block vuejs %}
<script>
new Vue({
  el: "#app",
  delimiters: ["[[", "]]"]
})
</script>
{% endblock %}

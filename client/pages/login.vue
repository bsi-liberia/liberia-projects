<template>
  <div>
    <h1>Login</h1>
    <p class="lead">Please log in to access this area.</p>
    <form @submit="login" class="form-horizontal">
      <b-form-group
        label="Username"
        label-cols-sm="2"
        for="username">
        <b-form-input v-model="username" name="username" id="username" ref="username" autocomplete="username" required></b-form-input>
      </b-form-group>
      <b-form-group
        label="Password"
        label-cols-sm="2"
        for="password">
        <b-form-input type="password" v-model="password" name="password" autocomplete="current-password" required></b-form-input>
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
          id="submit">Log in</button>
      </b-form-group>
      <b-form-group>
        <a href="users.reset_password">Forgot your password? Reset it here</a>.
      </b-form-group>
    </form>
  </div>
</template>
<script>
export default {
  middleware: ['auth'],
  data() {
    return {
      username: null,
      password: null,
      error: null
    }
  },
  computed: {
    redirect() {
      return (
        this.$route.query.redirect &&
        decodeURIComponent(this.$route.query.redirect)
      )
    },
    isCallback() {
      return Boolean(this.$route.query.callback)
    }
  },
  methods: {
    login(evt) {
      evt.preventDefault()
      this.$auth.loginWith('local', {
        data: {
          username: this.username,
          password: this.password
        }
      }).then(response => {
        this.$root.$bvToast.toast('Welcome back!', {
          title: `Logged in.`,
          variant: 'success',
          autoHideDelay: 500,
          solid: true
        })
      }).catch(error => {
        this.$bvToast.toast('Sorry, could not log in. Please check your password and try again.', {
          title: `Error.`,
          variant: 'danger',
          solid: true
        })
      }
      )
    }
  }
}
</script>

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
        <b-form-input type="password" v-model="password" name="password" autocomplete="password" required></b-form-input>
      </b-form-group>
      <b-form-group>
        <b-btn type="submit" variant="primary"
          id="submit">Log in</b-btn>
      </b-form-group>
      <b-form-group>
        <nuxt-link :to="{ name: 'users-reset-password'}">Forgot your password? Reset it here</nuxt-link>.
      </b-form-group>
    </form>
  </div>
</template>
<script>
import config from '~/nuxt.config'
export default {
  middleware: ['auth'],
  data() {
    return {
      username: null,
      password: null,
      remember: false,
      error: null
    }
  },
  head() {
    return {
      title: `Login | ${config.head.title}`
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

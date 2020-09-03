<template>
  <div>
    <h1>Reset password</h1>
    <p class="lead">Please check your email for a reset key. Either click the link in the email, or enter the key in the form below.</p>
    <b-form class="form-horizontal" @submit.stop.prevent="resetPasswordkey">
      <b-form-group
        label="Email address"
        label-cols-sm="2">
        <b-input type="text" class="form-control" v-model="email_address" required/>
      </b-form-group>
      <b-form-group
        label="Reset key"
        label-cols-sm="2">
        <b-input type="text" class="form-control" v-model="reset_password_key" required/>
      </b-form-group>
      <b-form-group>
        <b-btn type="submit" variant="primary">Reset password</b-btn>
      </b-form-group>
    </b-form>
  </div>
</template>
<script>
import config from '~/nuxt.config'
export default {
  data() {
    return {
      email_address: null,
      reset_password_key: null
    }
  },
  head() {
    return {
      title: `Reset password | ${config.head.title}`
    }
  },
  mounted: function() {
    if ('email_address' in this.$route.query) {
      this.email_address = this.$route.query.email_address
    }
    if ('reset_password_key' in this.$route.query) {
      this.reset_password_key = this.$route.query.reset_password_key
    }
    if (this.reset_password_key && this.email_address) {
      this.resetPasswordkey()
    }
  },
  methods: {
    resetPasswordkey: function() {
      this.$axios
        .post('reset-password/key/', {
          email_address: this.email_address,
          reset_password_key: this.reset_password_key
        })
        .then((response) => {
          this.$router.push({ name: 'users-reset-password-password', query: {
            email_address: this.email_address,
            reset_password_key: this.reset_password_key
          }})
        })
        .catch(error => {
          this.$root.$bvToast.toast(` ${ error.response.data.msg }`, {
            title: "Error.",
            autoHideDelay: 10000,
            variant: "danger"
          })
          this.$router.push({ name: 'users-reset-password', query: {
            email_address: this.email_address
          }})
        })
    }
  }
}
</script>

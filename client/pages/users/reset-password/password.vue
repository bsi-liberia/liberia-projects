<template>
  <div>
    <h1>Reset password</h1>
    <p class="lead">Please enter a new password below.</p>
    <b-form class="form-horizontal" @submit.stop.prevent="resetPassword">
      <b-form-group
        label="Password"
        label-cols-sm="2">
          <b-input type="password" class="form-control" v-model="password" required/>
      </b-form-group>
      <b-form-group
        label="Confirm password"
        label-cols-sm="2">
          <b-input type="password" class="form-control" v-model="password_2" required/>
      </b-form-group>
      <b-form-group>
        <b-btn type="submit">Reset password</b-btn>
      </b-form-group>
    </b-form>
  </div>
</template>
<script>
export default {
  data() {
    return {
      email_address: null,
      reset_password_key: null,
      password: null,
      password_2: null
    }
  },
  mounted: function() {
    if ('email_address' in this.$route.query) {
      this.email_address = this.$route.query.email_address
    }
    if ('reset_password_key' in this.$route.query) {
      this.reset_password_key = this.$route.query.reset_password_key
    }
    if (this.reset_password_key == null || this.email_address == null) {
      this.$router.push({ name: 'users-reset-password-key', query: {email_address: this.email_address}})
    }
  },
  methods: {
    resetPassword: function() {
      if (this.password != this.password_2) {
        this.$bvToast.toast(`Your passwords do not match. You must enter the same password twice.`, {
          title: "Error.",
          variant: "danger"
        })
        return
      }
      this.$axios
        .post('reset-password/password/', {
          email_address: this.email_address,
          reset_password_key: this.reset_password_key,
          password: this.password,
          password_2: this.password_2
        })
        .then((response) => {
          this.$root.$bvToast.toast(`Your password was successfully changed. You can log in with your new password.`, {
            title: 'Password changed',
            autoHideDelay: 10000,
            solid: true,
            variant: 'success'
          })
          this.$router.push({ name: 'login', query: {email_address: this.email_address}})
        })
        .catch(error => {
          this.$bvToast.toast(`Sorry, something went wrong, and your password could not be reset.`, {
            title: "Error.",
            variant: "danger"
          })
        })
    }
  }
}
</script>

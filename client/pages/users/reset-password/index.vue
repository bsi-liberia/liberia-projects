<template>
  <div>
    <h1>Reset password</h1>
    <p class="lead">Please enter your email address. If you have an account on the Liberia Projects Dashboard, you'll receive an email with instructions on how to reset your password.</p>
    <b-form class="form-horizontal" @submit.stop.prevent="resetPassword" >
      <b-form-group
        label="Email address"
        label-cols-sm="2">
          <b-input type="text" class="form-control" v-model="email_address" reuqired/>
      </b-form-group>
      <b-form-group>
        <b-btn type="submit" variant="primary">Reset password</b-btn>
      </b-form-group>
    </b-form>
  </div>
</template>
<script>
export default {
  data() {
    return {
      email_address: null
    }
  },
  methods: {
    resetPassword: function() {
      this.$axios
        .post('reset-password/', {email_address: this.email_address})
        .then((response) => {
          this.$router.push({ name: 'users-reset-password-key', query: {email_address: this.email_address}})
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
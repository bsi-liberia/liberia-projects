import { BVToastPlugin } from 'bootstrap-vue'

export default function ({ $axios, app, redirect }) {
  $axios.onError(error => {
    const code = parseInt(error.response && error.response.status)
    if ([401, 422].includes(code)) {
      if (app.router.app._route.name == "login") { return }
      app.router.app.$bvToast.toast(`Please login again.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger',
          to: "login"
        })
      app.$auth.logout()
      .then(() => {
        redirect('/login')
      })
    } else if ([500].includes(code)) {
      app.router.app.$bvToast.toast(`Sorry, there was an unexpected server error. The error was: ${error}. Please try again, or contact support if this problem persists.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger'
        })
    } else if (error.response == undefined) {
      app.router.app.$bvToast.toast(`Sorry, there was an error. It appears that you are not connected to the Internet.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger'
        })
    }
  })
}
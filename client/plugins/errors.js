
export default function ({ $axios, app, redirect }) {
  $axios.onError(error => {
    const code = parseInt(error.response && error.response.status)
    if ([401, 403, 422].includes(code)) {
      if (app.router.app._route.name == "login") { return }
      app.router.app.$bvToast.toast(`Please login to access this page.`, {
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
      Promise.reject(error)
    } else if ([404].includes(code)) {
      app.router.app.$bvToast.toast(`This page could not be found.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger'
        })
        Promise.reject(error)
    } else if ([500].includes(code)) {
      app.router.app.$bvToast.toast(`Sorry, there was an unexpected server error. The error was: ${error}. Please try again, or contact support if this problem persists.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger'
        })
        Promise.reject(error)
    } else if (error.response == undefined) {
      app.router.app.$bvToast.toast(`Sorry, there was an error. It appears that you are not connected to the Internet.`, {
          title: 'Error',
          autoHideDelay: 10000,
          solid: true,
          variant: 'danger'
        })
        Promise.reject(error)
    }
  })
}
export const state = () => ({
  unathenticatedUserDefaults: {
    "username": null,
    "administrator": false,
    "name": null,
    "permissions_list": {
        "edit": "none",
        "organisations": {},
        "view": "none"
    }, "roles_list": [],
    "email_address": null,
    "permissions_dict": {
        "edit": "none",
        "organisations": {},
        "view": "none"
    }
  }
})

export const mutations = {
  setUnauthenticatedUserDefaults(state, data) {
    state.unathenticatedUserDefaults = data
  }
}

export const actions = {
  async nuxtServerInit ({ commit }, { $axios }) {
    const userData = await $axios
      .$get(`unauthenticated_user/`)
    commit('setUnauthenticatedUserDefaults', userData.user)
  }
}

export const getters = {
  isAuthenticated(state) {
    return state.auth.loggedIn
  },
  loggedInUser(state) {
    if (state.auth.loggedIn) {
      return state.auth.user
    }
    return state.unathenticatedUserDefaults
  }
}

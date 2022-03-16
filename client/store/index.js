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
  },
  sectors: [],
  donors: [],
})

export const mutations = {
  setUnauthenticatedUserDefaults(state, data) {
    state.unathenticatedUserDefaults = data
  },
  setMtefSectors(state, data) {
    state.sectors = data.codelists.filter((sector) => {return sector.name != ''}).sort((a, b) => a.name > b.name ? 1 : -1);
  },
  setDonors(state, data) {
    state.donors = data.organisations.filter((donor) => {return donor.name != ''})
  },
}

export const actions = {
  async nuxtServerInit ({ commit }, { $axios }) {
    const userData = await $axios
      .$get(`unauthenticated_user/`)
    commit('setUnauthenticatedUserDefaults', userData.user)
    const mtefSectors = await $axios
      .$get(`codelists/mtef-sector/`)
    commit('setMtefSectors', mtefSectors)
    const donors = await $axios
      .$get(`codelists/organisations/donor/`)
    commit('setDonors', donors)
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

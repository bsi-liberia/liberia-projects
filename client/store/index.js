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
  sdgGoals: [],
  papdPillars: [],
  donors: [],
})

export const mutations = {
  setUnauthenticatedUserDefaults(state, data) {
    state.unathenticatedUserDefaults = data
  },
  setMtefSectors(state, data) {
    state.sectors = data.codelists.filter((sector) => {return sector.name != ''}).sort((a, b) => a.name > b.name ? 1 : -1);
  },
  setSDGGoals(state, data) {
    state.sdgGoals = data.codelists.filter((sdg) => {return sdg.name != ''}).sort((a, b) => a.id > b.id ? 1 : -1);
  },
  setPAPDPillars(state, data) {
    state.papdPillars = data.codelists.filter((papd) => {return papd.name != ''}).sort((a, b) => a.id > b.id ? 1 : -1);
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
    const sdgGoals = await $axios
      .$get(`codelists/sdg-goals/`)
    commit('setSDGGoals', sdgGoals)
    const papdPillars = await $axios
      .$get(`codelists/papd-pillar/`)
    commit('setPAPDPillars', papdPillars)
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

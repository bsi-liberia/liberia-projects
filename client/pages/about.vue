<template lang="md">
# About

The Liberia Project Dashboard (LPD) is an aid information management system used to input, analyze and publish information about development projects across the country. In essence, the LPD is a flagship indicator of a new era of aid management that will be guided both in principle and practice by the recently adopted [National Aid and NGO Policy of Liberia (NAPL)](https://www.mfdp.gov.lr/index.php/component/edocman/policy-procedure/national-aid-and-ngo-policy-of-liberia?Itemid=1757).

The objective is to improve compliance and build skills to mainstream the tool across GOL system. The full utilization of LPD will increase transparency and accountability both in the management of public sector investment projects and development assistance programmes.

The LPD will be rolled out as part of a National Conference under the theme “Programming Aid for National Development” organized by the Ministry of Finance and Development Planning scheduled for Friday, November, 27 2020 at the Ministerial Complex in Congo Town.

For more information please contact the Department of Economic Management at the Ministry of Finance and Development Planning.

---

### Supported by

<b-row class="text-center">
  <b-col md="4">
    <img src="~/assets/img/swedish-embassy.png" alt="Embassy of Sweden, Monrovia" />
  </b-col>
  <b-col md="4">
    <img src="~/assets/img/USAID.png" alt="USAID" height="60px" />
  </b-col>
  <b-col md="4">
    <img src="~/assets/img/afdb.png" alt="African Development Bank" height="60px" />
  </b-col>
</b-row>

</template>
<style scoped>
.header-anchor {
  display: none;
}
</style>
<script>
import { mapGetters } from 'vuex'
export default {
  data() {
    return {
    }
  },
  head() {
    return {
      title: `About | ${this.$config.title}`
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  },
  methods: {
  },
  mounted() {
  }
}
</script>
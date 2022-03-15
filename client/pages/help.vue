<template lang="md">
# Help

This section describes how to use the Dashboard, including updating data, generating reports, and exporting data.

----

## Updating data

### Reporting cycle

DPs are requested to provide the following data for each project:

* Once per quarter: total disbursements in the previous quarter. Data should be provided within 15 days after the end of the quarter.
* Once per year: forward disbursement projections (also known as MTEF Projections) by quarter for the next fiscal year, and by year for the subsequent two fiscal years.

Date | Required data
--- | ---
**January 15th** | Disbursement data for Q4 of the previous FY (October-December).
**April 15th** | Disbursement data for Q1 of this FY (January-March).
**July 15th** | Disbursement data for Q2 of this FY (April-June).
**August 15th** | Forward disbursement projections <br>*For the next FY (beginning January)*, broken down by quarter. <br>*For the subsequent two FYs*, broken down by year.
**October 15th** | Disbursement data for Q3 of this FY (July-September).

<template v-if="(loggedInUser.permissions_dict.edit != 'none') || (loggedInUser.roles_list.includes('desk-officer'))">

### Editing a single activity

Where users are authorised, updating data on a particular project is simple. From the <nuxt-link :to="{name: 'activities'}">Activities</nuxt-link> page, click the **Edit** icon to the right of any project. You will see the activity editor. As you click across the various tabs, you will see all the project data that can be edited, including:

* **Basic** - title, description, start and end dates, and other basic classifications of the project
* **Sectors** - the MTEF Sector, aligned ministry/agency, SDG Goals and PAPD Pillar
* **Locations** - the sub-national locations where this activity is active
* **Financials** - commitments (the total value of the project), disbursements, and forward spending plans (MTEF Projections).
* **Milestones** *(curently only for PSIP projects)* - select which milestones are now complete
* **Conditions** - add donors' expected counterpart funding *(in future, this tab will also allow the inclusion of effectiveness conditions)*

The activity editor is quite straightforward and quick to use; all data is saved as you edit and move through the interface.

However, sometimes you may want to update many activities at once. For this, you can use Excel update templates. The following sections describe how this works for the reporting of (quarterly) [disbursement data](#quarterly-update-of-disbursement-data) and (annual) [MTEF projections](#annual-update-of-mtef-projections-data).

---

### Quarterly update of disbursement data

In the past, it took a lot of effort each quarter to update disbursement data for every donor. This is now much simpler and faster, if you follow these steps:

1. On the <nuxt-link :to="{name: 'export'}">Export data</nuxt-link> tab, scroll down to `Excel reporting templates`
2. On the left hand side, under `Download template`, select the **Disbursements** template type.
3. Select a donor and currency (default is USD).
4. Optionally select additional columns to include in your template, using the `Customise columns` button.
5. Send the template _as an email attachment_ to the relevant donor. Ask them to update the quarterly disbursements column.

Review the file you receive back from the donor and check the numbers make sense. If you're happy, continue to the next section and import the file.

#### Importing the updated data
1. On the <nuxt-link :to="{name: 'export'}">Export data</nuxt-link> tab, scroll down to `Excel reporting templates`
2. On the right hand side, under `Import template`, select **Disbursements**, if it's not already selected.
3. Optionally select additional financial columns, to import disbursements for other fiscal quarters.
4. Upload the file you received back from the donor. All projects will be updated according to the data entered into the file by the donor.

The following fields will be automatically updated:

* Disbursement for relevant fical quarter(s)
* Donor project code
* Title
* Description
* Implementer
* Activity Status
* Activity Start Date
* Activity End Date

----

### Annual update of MTEF projections data

Each year, MTEF projections data has to be collected from donors for the forthcoming fiscal years, as part of the budget process. This should be a fairly straightforward process to collect and input this data, if you follow these steps:

1. On the <nuxt-link :to="{name: 'export'}">Export data</nuxt-link> tab, scroll down to `Excel reporting templates`
2. On the left hand side, under `Download template`, select the **MTEF projections** template type.
3. Select a donor and currency (default is USD).
4. Optionally select additional columns to include in your template, using the `Customise columns` button.
5. Send the template _as an email attachment_ to the relevant donor. Ask them to update the MTEF Projections column.

Review the file you receive back from the donor and check the numbers make sense. If you're happy, continue to the next section and import the file.

#### Importing the updated data
1. On the <nuxt-link :to="{name: 'export'}">Export data</nuxt-link> tab, scroll down to `Excel reporting templates`
2. On the right hand side, under `Import template`, select **MTEF Projections** template type, if it's not already selected.
3. Optionally select additional financial columns, to import MTEF projections for other years.
4. Upload the file you received back from the donor. All projects will be updated according to the data entered into the file by the donor.

The following fields will be automatically updated:

* MTEF Projections for relevant FY(s)
* Donor project code
* Title
* Description
* Implementer
* Activity Status
* Activity Start Date
* Activity End Date

</template>

---

## Reports and exports

### Standard reports

A number of standard reports are automatically updated as the data is updated throughout the system:

* On the <nuxt-link :to="{name: 'index'}">home page</nuxt-link>:
    * disbursements, projected disbursements, and new commitments by sector (you can select for a specific Fiscal Year)
    * change by sector over time (you can select to see this by disbursements, projected disbursements, or new commitments)
    * commitments and disbursements by sector and source to date
* On the reports drop-down (from the menu at the top of the page):
    * <nuxt-link :to="{name: 'reports-counterpart_funding'}">counterpart funding requirements</nuxt-link> (for AMCU projects)
    * <nuxt-link :to="{name: 'reports-milestones'}">milestone tracking</nuxt-link> (for PSIP projects)

You may not have access to all of these reports.

---

### Exporting data

There are a couple of ways of exporting data from the system.

1. If you want to generate an export of all activities, you can do so on the <nuxt-link :to="{name: 'export'}">Export data</nuxt-link> tab:
   * **Export data in Excel Format** will export data according to AMCU's existing Excel format.
   * **Download detailed AMCU financial transactions data for analysis** provides a more detailed and advanced format, useful for time-series analysis.
   * **Download integrated dataset of AMCU and PSIP projects** follows the same format as the AMCU Excel format, but includes also PSIP projects.
2. If you want to generate an export of a subsection of activities, you can filter for activities on the <nuxt-link :to="{name: 'activities'}">Activities</nuxt-link> tab and then click `Export selection to Excel`.
</template>
<style scoped>
h3 {
	margin-top: 10px;
}
table {
	width: 100%;
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
      title: `Help | ${this.$config.title}`
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
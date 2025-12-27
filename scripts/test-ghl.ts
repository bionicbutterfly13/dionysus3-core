import { HighLevel } from './index';

const ghl = new HighLevel({
  privateIntegrationToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImZOMFFhckVEUm55TzM1MXJOQ0QzIiwidmVyc2lvbiI6MSwiaWF0IjoxNzIyNTA4NzY0MzkzfQ.Ps_rYWqw6wD6rxSUnHe2OtNj_9lz1_fpfkWkGbLN_c4',
});

async function main() {
  try {
    console.log("Fetching workflows...");
    const workflows = await ghl.workflows.getWorkflow({
      locationId: 'fN0QarEDRnyO351rNCD3'
    });
    console.log("Workflows found:", JSON.stringify(workflows, null, 2));
  } catch (error: any) {
    console.error("Error:", error.message);
    if (error.response) {
      console.error("Response data:", JSON.stringify(error.response.data, null, 2));
    }
  }
}

main();

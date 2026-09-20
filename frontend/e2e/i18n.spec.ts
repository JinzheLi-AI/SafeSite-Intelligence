import { test, expect } from '@playwright/test';
import zh from '../../shared/locales/zh-CN.json';
const t=(key:string)=>(zh as Record<string,string>)[key];

test('language switches instantly, keeps form and route, and persists',async({page})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Safety, in clear view.'})).toBeVisible();
 await page.goto('/inspections');
 await page.getByLabel('Location',{exact:true}).fill('Preserved draft');
 const before=await page.evaluate(()=>performance.timeOrigin);
 await page.getByRole('button',{name:'中文',exact:true}).click();
 await expect(page.getByLabel(t('Location'),{exact:true})).toHaveValue('Preserved draft');
 expect(await page.evaluate(()=>performance.timeOrigin)).toBe(before);
 await expect(page).toHaveURL(/\/inspections$/);
 await page.reload();
 await expect(page.locator('html')).toHaveAttribute('lang','zh-CN');
 await expect(page.getByRole('button',{name:t('Analyze Site'),exact:true})).toBeVisible();
 await page.goto('/');
 await expect(page.getByRole('heading',{name:t('Safety, in clear view.')})).toBeVisible();
});

test('Chinese pages and jurisdiction options stay readable at laptop and mobile sizes',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'中文',exact:true}).click();
 for(const width of [1366,390]) {
  await page.setViewportSize({width,height:900});
  for(const route of ['/','/inspections','/incidents','/analyst','/knowledge']) {
   await page.goto(route);
   await expect(page.locator('html')).toHaveAttribute('lang','zh-CN');
   await expect(page.locator('h1')).toHaveCount(1);
   await expect(page.locator('h1')).toBeVisible();
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
   await page.screenshot({path:`test-results/zh-${width}-${route.slice(1)||'dashboard'}.png`,fullPage:true});
  }
 }
 const jurisdiction=page.getByLabel(t('Regulatory Jurisdiction'),{exact:true});
 await expect(jurisdiction).toHaveValue('HK-SAR');
 for(const code of ['CN','SG','MY']) {
  await expect(jurisdiction.locator(`option[value="${code}"]`)).toHaveJSProperty('disabled',true);
  await expect(jurisdiction.locator(`option[value="${code}"]`)).toContainText(t('Coming Soon'));
 }
 await expect(jurisdiction.locator('option[value="HK-SAR"]')).toContainText(t('Hong Kong SAR'));
});

test('Chinese inspection sends selected language and incident detail uses translated domain labels',async({page})=>{
 await page.goto('/inspections');await page.getByRole('button',{name:'中文',exact:true}).click();
 const request=page.waitForRequest(r=>r.url().endsWith('/analyze')&&r.method()==='POST');
 await page.getByRole('button',{name:t('Analyze Site'),exact:true}).click();
 expect((await request).headers()['x-safesite-language']).toBe('zh-CN');
 await expect(page.getByRole('heading',{name:t('Human Review Required')})).toBeVisible();
 await expect(page.getByText(t('CRITICAL'),{exact:true}).first()).toBeVisible();
 await page.getByRole('button',{name:t('Confirm Findings'),exact:true}).click();
 await page.getByRole('link',{name:t('Open primary incident')}).click();
 await expect(page.getByRole('button',{name:t('Start Rectification')})).toBeVisible();
 await expect(page.getByRole('heading',{name:t('Working at Height'),exact:true}).first()).toBeVisible();
 await page.screenshot({path:'test-results/zh-incident-detail.png',fullPage:true});
});

test('all six Chinese Analyst suggestions return translated verified results',async({page})=>{
 await page.goto('/analyst');await page.getByRole('button',{name:'中文',exact:true}).click();
 const suggestions=page.locator('.suggestion-grid button');
 await expect(suggestions).toHaveCount(6);
 for(let i=0;i<6;i++) {
  await suggestions.nth(i).click();
  await expect(page.getByRole('region',{name:t('Safety analytics result')})).toBeVisible();
  await expect(page.getByText(t('Database query · no LLM'),{exact:true})).toBeVisible();
 }
 await page.screenshot({path:'test-results/zh-analyst-result.png',fullPage:true});
});

test('official citation text and title remain original after language switching',async({page})=>{
 const excerpt='Original source passage describing fall protection and edge barriers.';
 await page.route('**/api/v1/knowledge/search',route=>route.fulfill({json:{status:'success',message:'Relevant official safety guidance retrieved.',candidate_count:1,latency_ms:2,citations:[{document_id:1,chunk_id:1,document_title:'Original Official Title',authority:'Hong Kong Labour Department',jurisdiction:'Hong Kong',document_type:'safety_guide',version:'Original edition',verified:true,active:true,source_url:'https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf',excerpt,section:'1.1',page_number:2,retrieval_score:.8}]}}));
 await page.goto('/knowledge');
 await page.getByLabel('Search official safety passages').fill('fall protection');
 await page.getByRole('button',{name:'Search verified guidance',exact:true}).click();
 await expect(page.getByText(excerpt,{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'中文',exact:true}).click();
 await expect(page.getByText(excerpt,{exact:true})).toBeVisible();
 await expect(page.getByText('Original Official Title',{exact:true})).toBeVisible();
 await expect(page.getByText(t('Official Source Text'),{exact:true})).toBeVisible();
 await page.screenshot({path:'test-results/zh-citation.png',fullPage:true});
});
